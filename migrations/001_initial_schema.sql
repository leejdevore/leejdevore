-- ============================================================================
-- DevSight NYC — Database Migration 001: Initial Schema
-- ============================================================================
-- Version: 1.0.0
-- Date: January 30, 2026
-- Description: Complete schema with version control, collaboration, and
--              auth-agnostic user model
-- ============================================================================

-- Prerequisites
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gist;  -- For exclusion constraints

-- ============================================================================
-- SECTION 1: USERS & WORKSPACES
-- ============================================================================

-------------------------------------------------------------------------------
-- 1.1 Users (Auth-Agnostic)
-------------------------------------------------------------------------------

CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity (nullable until auth)
    email               TEXT UNIQUE,
    name                TEXT,
    avatar_url          TEXT,

    -- Auth provider (Phase 1+)
    auth_provider       VARCHAR(20),
    auth_provider_id    TEXT,

    -- Anonymous tracking (Phase 0)
    anonymous_id        UUID UNIQUE,

    -- Display
    display_color       VARCHAR(7) DEFAULT '#' || LPAD(TO_HEX((RANDOM() * 16777215)::INT), 6, '0'),

    -- Preferences
    preferences         JSONB DEFAULT '{}',

    -- Spatial Web ID
    swid                TEXT UNIQUE,

    -- Timestamps
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at        TIMESTAMPTZ,

    CONSTRAINT unique_auth_provider UNIQUE (auth_provider, auth_provider_id)
);

CREATE INDEX idx_users_anonymous ON users(anonymous_id);
CREATE INDEX idx_users_email ON users(email);

-------------------------------------------------------------------------------
-- 1.2 Workspaces
-------------------------------------------------------------------------------

CREATE TABLE workspaces (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity
    name                TEXT NOT NULL,
    slug                VARCHAR(100) NOT NULL UNIQUE,
    description         TEXT,

    -- Type
    workspace_type      VARCHAR(20) NOT NULL DEFAULT 'personal',
    -- personal: auto-created for each user, single owner
    -- team: shared workspace with multiple members
    -- public: viewable by anyone (future)

    -- Owner (for personal workspaces)
    owner_id            UUID,

    -- Settings
    settings            JSONB DEFAULT '{}',

    -- Branding (future)
    logo_url            TEXT,

    -- Billing (future)
    plan_type           VARCHAR(20) DEFAULT 'free',

    swid                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT fk_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_workspaces_slug ON workspaces(slug);
CREATE INDEX idx_workspaces_owner ON workspaces(owner_id);
CREATE INDEX idx_workspaces_type ON workspaces(workspace_type);

-------------------------------------------------------------------------------
-- 1.3 Workspace Members
-------------------------------------------------------------------------------

CREATE TABLE workspace_members (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id        UUID NOT NULL,
    user_id             UUID NOT NULL,

    -- Role hierarchy: owner > admin > editor > viewer
    role                VARCHAR(20) NOT NULL DEFAULT 'editor',

    -- Invitation tracking
    invited_by          UUID,
    invited_at          TIMESTAMPTZ DEFAULT NOW(),
    joined_at           TIMESTAMPTZ,

    -- Status
    status              VARCHAR(20) DEFAULT 'active', -- active, pending, suspended

    created_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_workspace FOREIGN KEY (workspace_id)
        REFERENCES workspaces(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_invited_by FOREIGN KEY (invited_by)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT unique_membership UNIQUE (workspace_id, user_id),
    CONSTRAINT valid_role CHECK (role IN ('owner', 'admin', 'editor', 'viewer'))
);

CREATE INDEX idx_workspace_members_user ON workspace_members(user_id);
CREATE INDEX idx_workspace_members_workspace ON workspace_members(workspace_id);

-------------------------------------------------------------------------------
-- 1.4 User Sessions (Presence Tracking)
-------------------------------------------------------------------------------

CREATE TABLE user_sessions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL,

    -- Context
    workspace_id        UUID,
    project_id          UUID,

    -- Presence
    status              VARCHAR(20) DEFAULT 'online',
    last_heartbeat      TIMESTAMPTZ DEFAULT NOW(),

    -- Cursor (backup for Liveblocks)
    cursor_position     JSONB,
    current_bbl         BIGINT,

    -- Device
    user_agent          TEXT,

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    expires_at          TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours',

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_active ON user_sessions(last_heartbeat DESC) WHERE status = 'online';

-- ============================================================================
-- SECTION 2: PROJECTS & VERSION CONTROL
-- ============================================================================

-------------------------------------------------------------------------------
-- 2.1 Projects
-------------------------------------------------------------------------------

CREATE TABLE projects (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id        UUID NOT NULL,
    created_by          UUID NOT NULL,

    -- Identity
    name                TEXT NOT NULL,
    slug                VARCHAR(100) NOT NULL,
    description         TEXT,

    -- Display
    thumbnail_url       TEXT,
    color               VARCHAR(7),

    -- Default map state
    default_viewport    JSONB DEFAULT '{"center": [-73.98, 40.75], "zoom": 12}',
    default_layers      JSONB DEFAULT '["lots", "buildings"]',
    default_filters     JSONB DEFAULT '{}',

    -- Version control
    current_version_id  UUID,  -- FK added after versions table created

    -- Activity
    last_activity_at    TIMESTAMPTZ DEFAULT NOW(),
    last_activity_by    UUID,

    -- Sharing
    is_public           BOOLEAN DEFAULT FALSE,
    public_access_level VARCHAR(20) DEFAULT 'view', -- view, comment, edit
    share_token         VARCHAR(32) UNIQUE,

    swid                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT fk_workspace FOREIGN KEY (workspace_id)
        REFERENCES workspaces(id) ON DELETE CASCADE,
    CONSTRAINT fk_creator FOREIGN KEY (created_by)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT unique_project_slug UNIQUE (workspace_id, slug)
);

CREATE INDEX idx_projects_workspace ON projects(workspace_id);
CREATE INDEX idx_projects_activity ON projects(last_activity_at DESC);
CREATE INDEX idx_projects_share_token ON projects(share_token);

-------------------------------------------------------------------------------
-- 2.2 Project Versions (Snapshots)
-------------------------------------------------------------------------------

CREATE TABLE project_versions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL,
    created_by          UUID NOT NULL,

    -- Version info
    version_number      INTEGER NOT NULL,
    name                TEXT,  -- Optional name like "Pre-TDR Analysis" or "Final Review"
    description         TEXT,

    -- Snapshot type
    version_type        VARCHAR(20) NOT NULL DEFAULT 'manual',
    -- manual: user-created snapshot
    -- auto: automatic checkpoint (e.g., before major edit)
    -- milestone: marked as significant version

    -- Complete state snapshot (JSONB for flexibility)
    snapshot_data       JSONB NOT NULL,
    -- Structure:
    -- {
    --   "viewport": {...},
    --   "filters": {...},
    --   "layers": [...],
    --   "selected_sites": [...BBLs...],
    --   "site_lists": [{id, name, bbls, notes}],
    --   "analyses": [{type, config, results_summary}],
    --   "settings": {...}
    -- }

    -- Metadata
    snapshot_size_bytes INTEGER,

    -- Parent version (for branching, future)
    parent_version_id   UUID,

    -- Tags for filtering
    tags                TEXT[],

    created_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_creator FOREIGN KEY (created_by)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_parent FOREIGN KEY (parent_version_id)
        REFERENCES project_versions(id) ON DELETE SET NULL,
    CONSTRAINT unique_version_number UNIQUE (project_id, version_number)
);

CREATE INDEX idx_versions_project ON project_versions(project_id, version_number DESC);
CREATE INDEX idx_versions_type ON project_versions(version_type);
CREATE INDEX idx_versions_tags ON project_versions USING GIN(tags);

-- Add FK from projects to current version
ALTER TABLE projects
    ADD CONSTRAINT fk_current_version
    FOREIGN KEY (current_version_id)
    REFERENCES project_versions(id) ON DELETE SET NULL;

-------------------------------------------------------------------------------
-- 2.3 Version Comparisons (Cached Diffs)
-------------------------------------------------------------------------------

CREATE TABLE version_comparisons (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Versions being compared
    base_version_id     UUID NOT NULL,
    compare_version_id  UUID NOT NULL,

    -- Cached diff results
    diff_summary        JSONB NOT NULL,
    -- Structure:
    -- {
    --   "sites_added": [...BBLs...],
    --   "sites_removed": [...BBLs...],
    --   "filters_changed": {...before, after...},
    --   "analyses_added": [...],
    --   "analyses_removed": [...]
    -- }

    -- Stats
    total_changes       INTEGER,

    created_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_base FOREIGN KEY (base_version_id)
        REFERENCES project_versions(id) ON DELETE CASCADE,
    CONSTRAINT fk_compare FOREIGN KEY (compare_version_id)
        REFERENCES project_versions(id) ON DELETE CASCADE,
    CONSTRAINT unique_comparison UNIQUE (base_version_id, compare_version_id)
);

-- ============================================================================
-- SECTION 3: GEOSPATIAL SOURCE DATA
-- ============================================================================

-------------------------------------------------------------------------------
-- 3.1 Tax Lots (PLUTO)
-------------------------------------------------------------------------------

CREATE TABLE tax_lots (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity
    bbl                 BIGINT NOT NULL,
    borough             CHAR(2) NOT NULL,
    block               INTEGER NOT NULL,
    lot                 INTEGER NOT NULL,

    -- Spatial
    geom                GEOMETRY(MultiPolygon, 4326) NOT NULL,
    centroid            GEOMETRY(Point, 4326) GENERATED ALWAYS AS (ST_Centroid(geom)) STORED,
    lot_area_sf         NUMERIC(12,2),

    -- Address
    address             TEXT,
    zip_code            CHAR(5),

    -- Zoning
    zoning_dist_1       VARCHAR(12),
    zoning_dist_2       VARCHAR(12),
    zoning_dist_3       VARCHAR(12),
    zoning_dist_4       VARCHAR(12),
    commercial_overlay_1 VARCHAR(12),
    commercial_overlay_2 VARCHAR(12),
    special_district_1  VARCHAR(12),
    special_district_2  VARCHAR(12),
    special_district_3  VARCHAR(12),

    -- FAR
    resid_far           NUMERIC(5,2),
    comm_far            NUMERIC(5,2),
    facil_far           NUMERIC(5,2),
    built_far           NUMERIC(5,2),

    -- Building metrics
    bldg_area_sf        NUMERIC(12,2),
    res_area_sf         NUMERIC(12,2),
    office_area_sf      NUMERIC(12,2),
    retail_area_sf      NUMERIC(12,2),
    num_floors          INTEGER,
    num_bldgs           INTEGER,
    num_units           INTEGER,
    year_built          INTEGER,
    year_altered_1      INTEGER,
    year_altered_2      INTEGER,

    -- Classification
    bldg_class          CHAR(2),
    land_use            CHAR(2),
    owner_type          CHAR(1),
    owner_name          TEXT,

    -- Landmark
    landmark_status     VARCHAR(50),
    hist_district       VARCHAR(100),

    -- Assessment
    assessed_total      NUMERIC(14,2),
    assessed_land       NUMERIC(14,2),
    exempt_total        NUMERIC(14,2),

    -- Versioning (critical per your requirement)
    pluto_version       VARCHAR(10) NOT NULL,
    valid_from          DATE NOT NULL,
    valid_to            DATE,  -- NULL = current

    swid                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_bbl_version UNIQUE (bbl, pluto_version)
);

CREATE INDEX idx_lots_geom ON tax_lots USING GIST(geom);
CREATE INDEX idx_lots_bbl ON tax_lots(bbl);
CREATE INDEX idx_lots_bbl_current ON tax_lots(bbl) WHERE valid_to IS NULL;
CREATE INDEX idx_lots_version ON tax_lots(pluto_version);
CREATE INDEX idx_lots_zoning ON tax_lots(zoning_dist_1);

-- View for current lots only
CREATE VIEW current_tax_lots AS
SELECT * FROM tax_lots WHERE valid_to IS NULL;

-------------------------------------------------------------------------------
-- 3.2 Buildings
-------------------------------------------------------------------------------

CREATE TABLE buildings (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bin                 BIGINT NOT NULL,
    bbl                 BIGINT NOT NULL,

    -- Spatial
    geom                GEOMETRY(MultiPolygon, 4326),
    ground_elev_ft      NUMERIC(8,2),
    height_roof_ft      NUMERIC(8,2),

    -- Attributes
    name                TEXT,
    construction_year   INTEGER,
    doitt_id            BIGINT,

    -- LL97
    ll97_covered        BOOLEAN DEFAULT FALSE,

    -- Versioning
    source_version      VARCHAR(20),
    valid_from          DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_to            DATE,

    swid                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_buildings_bbl ON buildings(bbl);
CREATE INDEX idx_buildings_bin ON buildings(bin);
CREATE INDEX idx_buildings_geom ON buildings USING GIST(geom);
CREATE INDEX idx_buildings_current ON buildings(bbl) WHERE valid_to IS NULL;

-------------------------------------------------------------------------------
-- 3.3 Landmarks
-------------------------------------------------------------------------------

CREATE TABLE landmarks (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lpc_id              VARCHAR(20),
    bbl                 BIGINT,
    bin                 BIGINT,

    -- Spatial
    geom                GEOMETRY(MultiPolygon, 4326),

    -- Details
    name                TEXT NOT NULL,
    designation_date    DATE,
    landmark_type       VARCHAR(50),

    -- TDR potential
    has_unused_far      BOOLEAN DEFAULT FALSE,
    unused_far_sf       NUMERIC(12,2),
    is_74_79_eligible   BOOLEAN DEFAULT TRUE,

    swid                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_landmarks_bbl ON landmarks(bbl);
CREATE INDEX idx_landmarks_geom ON landmarks USING GIST(geom);

-------------------------------------------------------------------------------
-- 3.4 Zoning Districts (Reference)
-------------------------------------------------------------------------------

CREATE TABLE zoning_districts (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    district_code       VARCHAR(12) NOT NULL UNIQUE,
    district_type       VARCHAR(20) NOT NULL,

    -- FAR limits
    base_resid_far      NUMERIC(5,2),
    base_comm_far       NUMERIC(5,2),
    base_facil_far      NUMERIC(5,2),
    max_resid_far       NUMERIC(5,2),
    max_comm_far        NUMERIC(5,2),

    -- Height
    max_height_ft       INTEGER,
    sky_exposure_plane  BOOLEAN DEFAULT FALSE,

    description         TEXT,

    -- Effective dates for regulation changes
    effective_from      DATE,
    effective_to        DATE,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-------------------------------------------------------------------------------
-- 3.5 LL84 Energy Reports
-------------------------------------------------------------------------------

CREATE TABLE ll84_energy_reports (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bbl                 BIGINT NOT NULL,
    bin                 BIGINT,
    property_id         BIGINT,

    -- Period
    report_year         INTEGER NOT NULL,

    -- Building info
    property_name       TEXT,
    address             TEXT,
    primary_use         VARCHAR(100),
    gross_floor_area_sf NUMERIC(12,2),
    year_built          INTEGER,

    -- Energy
    site_eui            NUMERIC(8,2),
    source_eui          NUMERIC(8,2),
    weather_norm_site_eui NUMERIC(8,2),

    -- Fuel breakdown
    electricity_use_kbtu    NUMERIC(14,2),
    natural_gas_use_kbtu    NUMERIC(14,2),
    fuel_oil_use_kbtu       NUMERIC(14,2),
    district_steam_use_kbtu NUMERIC(14,2),

    -- Emissions
    total_ghg_emissions_mtco2e NUMERIC(10,2),
    direct_ghg_emissions       NUMERIC(10,2),
    indirect_ghg_emissions     NUMERIC(10,2),

    energy_star_score   INTEGER,
    data_quality_flag   VARCHAR(20),

    swid                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_bbl_year UNIQUE (bbl, report_year)
);

CREATE INDEX idx_ll84_bbl ON ll84_energy_reports(bbl);
CREATE INDEX idx_ll84_year ON ll84_energy_reports(report_year);

-- ============================================================================
-- SECTION 4: ANALYSIS TABLES
-- ============================================================================

-------------------------------------------------------------------------------
-- 4.1 TDR Scenarios (with Sharing)
-------------------------------------------------------------------------------

CREATE TABLE tdr_scenarios (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Ownership
    project_id          UUID,
    created_by          UUID NOT NULL,

    -- Target
    target_bbl          BIGINT NOT NULL,
    target_address      TEXT,

    -- Details
    name                TEXT NOT NULL,
    description         TEXT,

    -- Calculated totals
    base_buildable_sf       NUMERIC(12,2),
    total_tdr_acquired_sf   NUMERIC(12,2),
    total_achievable_sf     NUMERIC(12,2),
    estimated_tdr_cost      NUMERIC(14,2),

    -- Status
    status              VARCHAR(20) DEFAULT 'draft',

    -- Version control for scenarios
    version             INTEGER DEFAULT 1,
    parent_scenario_id  UUID,  -- For "Save As" / branching

    swid                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT fk_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE SET NULL,
    CONSTRAINT fk_creator FOREIGN KEY (created_by)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_parent FOREIGN KEY (parent_scenario_id)
        REFERENCES tdr_scenarios(id) ON DELETE SET NULL
);

CREATE INDEX idx_tdr_scenarios_project ON tdr_scenarios(project_id);
CREATE INDEX idx_tdr_scenarios_user ON tdr_scenarios(created_by);
CREATE INDEX idx_tdr_scenarios_target ON tdr_scenarios(target_bbl);

-------------------------------------------------------------------------------
-- 4.2 Scenario Sharing (Granular Permissions)
-------------------------------------------------------------------------------

CREATE TABLE scenario_shares (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id         UUID NOT NULL,

    -- Share target (one of these)
    shared_with_user_id     UUID,
    shared_with_workspace_id UUID,

    -- Permission level
    permission          VARCHAR(20) NOT NULL DEFAULT 'view',
    -- view: can see scenario
    -- comment: can add comments
    -- edit: can modify
    -- admin: can share with others

    -- Share metadata
    shared_by           UUID NOT NULL,
    shared_at           TIMESTAMPTZ DEFAULT NOW(),

    -- Expiration (optional)
    expires_at          TIMESTAMPTZ,

    CONSTRAINT fk_scenario FOREIGN KEY (scenario_id)
        REFERENCES tdr_scenarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_shared_with_user FOREIGN KEY (shared_with_user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_shared_with_workspace FOREIGN KEY (shared_with_workspace_id)
        REFERENCES workspaces(id) ON DELETE CASCADE,
    CONSTRAINT fk_shared_by FOREIGN KEY (shared_by)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT valid_permission CHECK (permission IN ('view', 'comment', 'edit', 'admin')),
    CONSTRAINT has_share_target CHECK (
        (shared_with_user_id IS NOT NULL AND shared_with_workspace_id IS NULL) OR
        (shared_with_user_id IS NULL AND shared_with_workspace_id IS NOT NULL)
    )
);

CREATE INDEX idx_scenario_shares_scenario ON scenario_shares(scenario_id);
CREATE INDEX idx_scenario_shares_user ON scenario_shares(shared_with_user_id);
CREATE INDEX idx_scenario_shares_workspace ON scenario_shares(shared_with_workspace_id);

-------------------------------------------------------------------------------
-- 4.3 TDR Sources
-------------------------------------------------------------------------------

CREATE TABLE tdr_sources (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id         UUID NOT NULL,

    -- Source
    source_bbl          BIGINT NOT NULL,
    source_address      TEXT,

    -- Transfer type
    transfer_type       VARCHAR(20) NOT NULL,

    -- Quantities
    available_sf        NUMERIC(12,2) NOT NULL,
    selected_sf         NUMERIC(12,2) NOT NULL,

    -- Cost
    price_per_sf        NUMERIC(8,2),
    estimated_cost      NUMERIC(14,2),

    -- Constraints
    max_transferable_sf NUMERIC(12,2),
    constraint_notes    TEXT,

    -- Toggle
    is_included         BOOLEAN DEFAULT TRUE,

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_scenario FOREIGN KEY (scenario_id)
        REFERENCES tdr_scenarios(id) ON DELETE CASCADE,
    CONSTRAINT valid_transfer_type CHECK (
        transfer_type IN ('ZLM', 'LANDMARK_74_79', 'SPECIAL_DISTRICT')
    )
);

CREATE INDEX idx_tdr_sources_scenario ON tdr_sources(scenario_id);

-------------------------------------------------------------------------------
-- 4.4 LL97 Calculations
-------------------------------------------------------------------------------

CREATE TABLE ll97_calculations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bbl                 BIGINT NOT NULL,
    bin                 BIGINT,

    ll84_report_id      UUID,
    calculation_date    DATE NOT NULL,

    -- Building
    building_use_type   VARCHAR(50) NOT NULL,
    gross_floor_area_sf NUMERIC(12,2) NOT NULL,

    -- Thresholds
    threshold_2024_kgco2e_sf NUMERIC(8,4),
    threshold_2030_kgco2e_sf NUMERIC(8,4),
    threshold_2035_kgco2e_sf NUMERIC(8,4),

    -- Actual
    actual_emissions_kgco2e_sf NUMERIC(8,4),

    -- Excess
    excess_2024_kgco2e_sf NUMERIC(8,4),
    excess_2030_kgco2e_sf NUMERIC(8,4),
    excess_2035_kgco2e_sf NUMERIC(8,4),

    -- Penalties
    penalty_2024        NUMERIC(12,2),
    penalty_2030        NUMERIC(12,2),
    penalty_2035        NUMERIC(12,2),

    -- Compliance
    compliant_2024      BOOLEAN,
    compliant_2030      BOOLEAN,
    compliant_2035      BOOLEAN,

    -- Distress
    distress_score      INTEGER,
    distress_factors    JSONB,

    swid                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_ll84 FOREIGN KEY (ll84_report_id)
        REFERENCES ll84_energy_reports(id) ON DELETE SET NULL
);

CREATE INDEX idx_ll97_bbl ON ll97_calculations(bbl);
CREATE INDEX idx_ll97_compliance ON ll97_calculations(compliant_2024, compliant_2030);
CREATE INDEX idx_ll97_distress ON ll97_calculations(distress_score DESC);

-------------------------------------------------------------------------------
-- 4.5 Opportunity Scores
-------------------------------------------------------------------------------

CREATE TABLE opportunity_scores (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bbl                 BIGINT NOT NULL UNIQUE,

    -- Components (0-100)
    development_potential_score INTEGER,
    air_rights_access_score     INTEGER,
    market_momentum_score       INTEGER,
    ll97_risk_score             INTEGER,

    -- Composite
    overall_score       INTEGER NOT NULL,

    -- Inputs
    built_far_pct       NUMERIC(5,2),
    unbuilt_sf          NUMERIC(12,2),
    adjacent_tdr_sf     NUMERIC(12,2),
    landmark_tdr_sf     NUMERIC(12,2),
    rent_yoy_pct        NUMERIC(5,2),
    ll97_penalty_2030   NUMERIC(12,2),

    -- Meta
    calculated_at       TIMESTAMPTZ NOT NULL,
    algorithm_version   VARCHAR(10) NOT NULL,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_opp_score ON opportunity_scores(overall_score DESC);

-- ============================================================================
-- SECTION 5: COLLABORATION
-- ============================================================================

-------------------------------------------------------------------------------
-- 5.1 Spatial Comments (Figma-style 2-level threading)
-------------------------------------------------------------------------------

CREATE TABLE spatial_comments (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Ownership
    project_id          UUID NOT NULL,
    user_id             UUID NOT NULL,

    -- Spatial anchor
    anchor_type         VARCHAR(20) NOT NULL,
    anchor_bbl          BIGINT,
    anchor_point        GEOMETRY(Point, 4326),
    anchor_viewport     JSONB,

    -- Threading (max 2 levels: parent + replies)
    parent_id           UUID,
    -- If parent_id IS NULL: this is a top-level comment
    -- If parent_id IS NOT NULL: this is a reply (and cannot have replies itself)

    -- Content
    content             TEXT NOT NULL,
    attachments         JSONB,

    -- Mentions
    mentioned_user_ids  UUID[],

    -- Status
    is_resolved         BOOLEAN DEFAULT FALSE,
    resolved_by         UUID,
    resolved_at         TIMESTAMPTZ,

    swid                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT fk_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_parent FOREIGN KEY (parent_id)
        REFERENCES spatial_comments(id) ON DELETE CASCADE,
    CONSTRAINT fk_resolved_by FOREIGN KEY (resolved_by)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT valid_anchor CHECK (anchor_type IN ('BBL', 'COORDINATES', 'VIEWPORT'))
);

CREATE INDEX idx_comments_project ON spatial_comments(project_id);
CREATE INDEX idx_comments_parent ON spatial_comments(parent_id);
CREATE INDEX idx_comments_bbl ON spatial_comments(anchor_bbl);
CREATE INDEX idx_comments_geom ON spatial_comments USING GIST(anchor_point);
CREATE INDEX idx_comments_active ON spatial_comments(project_id, created_at DESC)
    WHERE deleted_at IS NULL;

-- Trigger to enforce 2-level threading (Figma-style)
CREATE OR REPLACE FUNCTION enforce_comment_depth()
RETURNS TRIGGER AS $$
BEGIN
    -- If this is a reply (has parent_id)
    IF NEW.parent_id IS NOT NULL THEN
        -- Check if parent is already a reply
        IF EXISTS (
            SELECT 1 FROM spatial_comments
            WHERE id = NEW.parent_id AND parent_id IS NOT NULL
        ) THEN
            RAISE EXCEPTION 'Cannot reply to a reply. Comments support only 2 levels (Figma-style).';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_comment_depth
    BEFORE INSERT OR UPDATE ON spatial_comments
    FOR EACH ROW
    EXECUTE FUNCTION enforce_comment_depth();

-------------------------------------------------------------------------------
-- 5.2 Site Lists
-------------------------------------------------------------------------------

CREATE TABLE site_lists (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL,
    created_by          UUID NOT NULL,

    name                TEXT NOT NULL,
    description         TEXT,
    color               VARCHAR(7),
    icon                VARCHAR(50),

    -- Ordering within project
    sort_order          INTEGER DEFAULT 0,

    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,

    CONSTRAINT fk_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_creator FOREIGN KEY (created_by)
        REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_site_lists_project ON site_lists(project_id);

CREATE TABLE site_list_items (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id             UUID NOT NULL,
    bbl                 BIGINT NOT NULL,

    notes               TEXT,
    sort_order          INTEGER DEFAULT 0,

    added_by            UUID,
    added_at            TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_list FOREIGN KEY (list_id)
        REFERENCES site_lists(id) ON DELETE CASCADE,
    CONSTRAINT fk_added_by FOREIGN KEY (added_by)
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT unique_list_bbl UNIQUE (list_id, bbl)
);

CREATE INDEX idx_site_list_items_list ON site_list_items(list_id);
CREATE INDEX idx_site_list_items_bbl ON site_list_items(bbl);

-------------------------------------------------------------------------------
-- 5.3 Saved Views
-------------------------------------------------------------------------------

CREATE TABLE saved_views (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL,
    created_by          UUID NOT NULL,

    name                TEXT NOT NULL,
    description         TEXT,

    -- State
    viewport            JSONB NOT NULL,
    visible_layers      JSONB,
    filters             JSONB,
    selected_bbls       BIGINT[],

    -- Sharing
    is_public           BOOLEAN DEFAULT FALSE,
    share_token         VARCHAR(32) UNIQUE,

    swid                TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_creator FOREIGN KEY (created_by)
        REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_views_project ON saved_views(project_id);
CREATE INDEX idx_views_share_token ON saved_views(share_token);

-------------------------------------------------------------------------------
-- 5.4 Activity Log (Audit Trail)
-------------------------------------------------------------------------------

CREATE TABLE activity_log (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Context
    user_id             UUID,
    workspace_id        UUID,
    project_id          UUID,

    -- Action
    action_type         VARCHAR(50) NOT NULL,
    -- Examples: project.created, version.created, comment.added,
    --           scenario.shared, site.added, filter.changed

    -- Target entity
    entity_type         VARCHAR(50),
    entity_id           UUID,

    -- Details
    details             JSONB,

    -- IP/device (for security)
    ip_address          INET,
    user_agent          TEXT,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activity_user ON activity_log(user_id, created_at DESC);
CREATE INDEX idx_activity_project ON activity_log(project_id, created_at DESC);
CREATE INDEX idx_activity_type ON activity_log(action_type);

-- ============================================================================
-- SECTION 6: MARKET DATA (TimescaleDB)
-- ============================================================================

-- Note: Run CREATE EXTENSION timescaledb; separately if using TimescaleDB

-------------------------------------------------------------------------------
-- 6.1 Rent Observations
-------------------------------------------------------------------------------

CREATE TABLE rent_observations (
    time                TIMESTAMPTZ NOT NULL,
    nta_code            VARCHAR(10) NOT NULL,
    zip_code            CHAR(5),

    median_rent         NUMERIC(10,2),
    median_rent_psf     NUMERIC(8,2),
    asking_rent_avg     NUMERIC(10,2),

    available_units     INTEGER,
    vacancy_rate        NUMERIC(5,2),

    data_source         VARCHAR(50),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable if TimescaleDB is available
-- SELECT create_hypertable('rent_observations', 'time', if_not_exists => TRUE);

CREATE INDEX idx_rent_nta ON rent_observations(nta_code, time DESC);

-------------------------------------------------------------------------------
-- 6.2 Permit Activity
-------------------------------------------------------------------------------

CREATE TABLE permit_activity (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_number          VARCHAR(20) NOT NULL,

    bbl                 BIGINT,
    bin                 BIGINT,
    address             TEXT,
    zip_code            CHAR(5),
    borough             CHAR(2),

    job_type            VARCHAR(10),
    work_type           VARCHAR(100),
    permit_status       VARCHAR(50),
    permit_type         VARCHAR(50),

    filing_date         DATE,
    issuance_date       DATE,
    expiration_date     DATE,

    proposed_stories    INTEGER,
    proposed_units      INTEGER,
    proposed_sf         NUMERIC(12,2),
    estimated_cost      NUMERIC(14,2),

    data_source_date    DATE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_permits_bbl ON permit_activity(bbl);
CREATE INDEX idx_permits_date ON permit_activity(filing_date DESC);
CREATE INDEX idx_permits_type ON permit_activity(job_type);

-- ============================================================================
-- SECTION 7: HELPER FUNCTIONS
-- ============================================================================

-------------------------------------------------------------------------------
-- 7.1 Get or Create Anonymous User
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION get_or_create_anonymous_user(anon_id UUID)
RETURNS UUID AS $$
DECLARE
    user_id UUID;
    workspace_id UUID;
BEGIN
    -- Find existing user
    SELECT id INTO user_id FROM users WHERE anonymous_id = anon_id;

    IF user_id IS NULL THEN
        -- Create new user
        INSERT INTO users (anonymous_id, name, display_color)
        VALUES (
            anon_id,
            'User ' || LEFT(anon_id::TEXT, 8),
            '#' || LPAD(TO_HEX((RANDOM() * 16777215)::INT), 6, '0')
        )
        RETURNING id INTO user_id;

        -- Create personal workspace
        INSERT INTO workspaces (name, slug, workspace_type, owner_id)
        VALUES (
            'Personal',
            'personal-' || user_id::TEXT,
            'personal',
            user_id
        )
        RETURNING id INTO workspace_id;

        -- Add as owner
        INSERT INTO workspace_members (workspace_id, user_id, role, joined_at)
        VALUES (workspace_id, user_id, 'owner', NOW());
    END IF;

    RETURN user_id;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
-- 7.2 Link Anonymous User to Auth
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION link_anonymous_to_auth(
    anon_uuid UUID,
    auth_provider_name TEXT,
    auth_provider_user_id TEXT,
    user_email TEXT,
    user_name TEXT
) RETURNS UUID AS $$
DECLARE
    existing_user_id UUID;
BEGIN
    SELECT id INTO existing_user_id FROM users WHERE anonymous_id = anon_uuid;

    IF existing_user_id IS NOT NULL THEN
        UPDATE users SET
            email = user_email,
            name = COALESCE(user_name, name),
            auth_provider = auth_provider_name,
            auth_provider_id = auth_provider_user_id,
            updated_at = NOW()
        WHERE id = existing_user_id;

        -- Update personal workspace name
        UPDATE workspaces
        SET name = COALESCE(user_name, 'Personal') || '''s Workspace'
        WHERE owner_id = existing_user_id AND workspace_type = 'personal';

        RETURN existing_user_id;
    ELSE
        INSERT INTO users (email, name, auth_provider, auth_provider_id)
        VALUES (user_email, user_name, auth_provider_name, auth_provider_user_id)
        RETURNING id INTO existing_user_id;

        -- Create personal workspace for new auth user
        PERFORM create_personal_workspace(existing_user_id, user_name);

        RETURN existing_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
-- 7.3 Create Personal Workspace
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION create_personal_workspace(
    p_user_id UUID,
    p_user_name TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    workspace_id UUID;
BEGIN
    INSERT INTO workspaces (name, slug, workspace_type, owner_id)
    VALUES (
        COALESCE(p_user_name, 'Personal') || '''s Workspace',
        'personal-' || p_user_id::TEXT,
        'personal',
        p_user_id
    )
    RETURNING id INTO workspace_id;

    INSERT INTO workspace_members (workspace_id, user_id, role, joined_at)
    VALUES (workspace_id, p_user_id, 'owner', NOW());

    RETURN workspace_id;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
-- 7.4 Create Project Version (Snapshot)
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION create_project_version(
    p_project_id UUID,
    p_user_id UUID,
    p_name TEXT DEFAULT NULL,
    p_description TEXT DEFAULT NULL,
    p_version_type VARCHAR(20) DEFAULT 'manual',
    p_snapshot_data JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    v_version_number INTEGER;
    v_version_id UUID;
BEGIN
    -- Get next version number
    SELECT COALESCE(MAX(version_number), 0) + 1
    INTO v_version_number
    FROM project_versions
    WHERE project_id = p_project_id;

    -- Create version
    INSERT INTO project_versions (
        project_id, created_by, version_number, name, description,
        version_type, snapshot_data
    ) VALUES (
        p_project_id, p_user_id, v_version_number,
        COALESCE(p_name, 'Version ' || v_version_number),
        p_description, p_version_type, p_snapshot_data
    )
    RETURNING id INTO v_version_id;

    -- Update project's current version
    UPDATE projects
    SET current_version_id = v_version_id, updated_at = NOW()
    WHERE id = p_project_id;

    -- Log activity
    INSERT INTO activity_log (user_id, project_id, action_type, entity_type, entity_id, details)
    VALUES (p_user_id, p_project_id, 'version.created', 'project_version', v_version_id,
            jsonb_build_object('version_number', v_version_number, 'type', p_version_type));

    RETURN v_version_id;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
-- 7.5 Restore Project to Version
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION restore_project_to_version(
    p_project_id UUID,
    p_version_id UUID,
    p_user_id UUID
) RETURNS UUID AS $$
DECLARE
    v_new_version_id UUID;
    v_snapshot JSONB;
    v_source_version INTEGER;
BEGIN
    -- Get the snapshot data from target version
    SELECT snapshot_data, version_number
    INTO v_snapshot, v_source_version
    FROM project_versions
    WHERE id = p_version_id AND project_id = p_project_id;

    IF v_snapshot IS NULL THEN
        RAISE EXCEPTION 'Version not found';
    END IF;

    -- Create new version as restore point
    SELECT create_project_version(
        p_project_id,
        p_user_id,
        'Restored from Version ' || v_source_version,
        'Restored to state from version ' || v_source_version,
        'manual',
        v_snapshot
    ) INTO v_new_version_id;

    -- Log activity
    INSERT INTO activity_log (user_id, project_id, action_type, entity_type, entity_id, details)
    VALUES (p_user_id, p_project_id, 'version.restored', 'project_version', p_version_id,
            jsonb_build_object('restored_from', v_source_version));

    RETURN v_new_version_id;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------------------------------
-- 7.6 Generate SWID
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION generate_swid(
    entity_type TEXT,
    namespace TEXT,
    unique_part TEXT
) RETURNS TEXT AS $$
BEGIN
    RETURN 'did:swid:' || entity_type || ':' || namespace || ':' || unique_part;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-------------------------------------------------------------------------------
-- 7.7 Check User Has Scenario Access
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_can_access_scenario(
    p_user_id UUID,
    p_scenario_id UUID,
    p_required_permission VARCHAR(20) DEFAULT 'view'
) RETURNS BOOLEAN AS $$
DECLARE
    v_creator_id UUID;
    v_project_id UUID;
    v_share_permission VARCHAR(20);
    v_permission_hierarchy INTEGER;
BEGIN
    -- Permission hierarchy: view=1, comment=2, edit=3, admin=4
    v_permission_hierarchy := CASE p_required_permission
        WHEN 'view' THEN 1
        WHEN 'comment' THEN 2
        WHEN 'edit' THEN 3
        WHEN 'admin' THEN 4
        ELSE 0
    END;

    -- Check if user is creator
    SELECT created_by, project_id INTO v_creator_id, v_project_id
    FROM tdr_scenarios WHERE id = p_scenario_id;

    IF v_creator_id = p_user_id THEN
        RETURN TRUE;
    END IF;

    -- Check direct share
    SELECT permission INTO v_share_permission
    FROM scenario_shares
    WHERE scenario_id = p_scenario_id
      AND shared_with_user_id = p_user_id
      AND (expires_at IS NULL OR expires_at > NOW());

    IF v_share_permission IS NOT NULL THEN
        RETURN (CASE v_share_permission
            WHEN 'view' THEN 1
            WHEN 'comment' THEN 2
            WHEN 'edit' THEN 3
            WHEN 'admin' THEN 4
            ELSE 0
        END) >= v_permission_hierarchy;
    END IF;

    -- Check workspace share
    SELECT ss.permission INTO v_share_permission
    FROM scenario_shares ss
    JOIN workspace_members wm ON wm.workspace_id = ss.shared_with_workspace_id
    WHERE ss.scenario_id = p_scenario_id
      AND wm.user_id = p_user_id
      AND (ss.expires_at IS NULL OR ss.expires_at > NOW());

    IF v_share_permission IS NOT NULL THEN
        RETURN (CASE v_share_permission
            WHEN 'view' THEN 1
            WHEN 'comment' THEN 2
            WHEN 'edit' THEN 3
            WHEN 'admin' THEN 4
            ELSE 0
        END) >= v_permission_hierarchy;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SECTION 8: MATERIALIZED VIEWS
-- ============================================================================

-------------------------------------------------------------------------------
-- 8.1 Lots Enriched (Main Map Query)
-------------------------------------------------------------------------------

CREATE MATERIALIZED VIEW lots_enriched AS
SELECT
    tl.id,
    tl.bbl,
    tl.borough,
    tl.address,
    tl.geom,
    tl.centroid,
    tl.lot_area_sf,
    tl.zoning_dist_1,
    tl.special_district_1,

    -- FAR
    tl.resid_far,
    tl.comm_far,
    GREATEST(COALESCE(tl.resid_far, 0), COALESCE(tl.comm_far, 0)) AS max_far,
    tl.built_far,
    CASE
        WHEN GREATEST(COALESCE(tl.resid_far, 0), COALESCE(tl.comm_far, 0)) > 0
        THEN ROUND((tl.built_far / GREATEST(tl.resid_far, tl.comm_far, 0.01)) * 100, 1)
        ELSE NULL
    END AS built_far_pct,

    -- Unbuilt
    CASE
        WHEN tl.lot_area_sf > 0 AND GREATEST(COALESCE(tl.resid_far, 0), COALESCE(tl.comm_far, 0)) > 0
        THEN ROUND((GREATEST(tl.resid_far, tl.comm_far) - COALESCE(tl.built_far, 0)) * tl.lot_area_sf, 0)
        ELSE 0
    END AS unbuilt_sf,

    -- Building
    tl.bldg_area_sf,
    tl.num_floors,
    tl.year_built,
    tl.bldg_class,
    tl.owner_name,
    tl.owner_type,

    -- Landmark
    tl.landmark_status,
    CASE WHEN tl.landmark_status IS NOT NULL THEN TRUE ELSE FALSE END AS is_landmark,

    -- LL97
    ll97.compliant_2024,
    ll97.compliant_2030,
    ll97.penalty_2024,
    ll97.penalty_2030,
    ll97.distress_score,

    -- Opportunity
    os.overall_score AS opportunity_score,
    os.development_potential_score,

    tl.updated_at

FROM tax_lots tl
LEFT JOIN ll97_calculations ll97 ON ll97.bbl = tl.bbl
LEFT JOIN opportunity_scores os ON os.bbl = tl.bbl
WHERE tl.valid_to IS NULL;

CREATE UNIQUE INDEX idx_lots_enriched_bbl ON lots_enriched(bbl);
CREATE INDEX idx_lots_enriched_geom ON lots_enriched USING GIST(geom);
CREATE INDEX idx_lots_enriched_built_pct ON lots_enriched(built_far_pct);
CREATE INDEX idx_lots_enriched_unbuilt ON lots_enriched(unbuilt_sf DESC);
CREATE INDEX idx_lots_enriched_opp ON lots_enriched(opportunity_score DESC);

-------------------------------------------------------------------------------
-- 8.2 TDR Potential by Lot
-------------------------------------------------------------------------------

CREATE MATERIALIZED VIEW tdr_potential_by_lot AS
WITH adjacent_lots AS (
    SELECT
        a.bbl AS target_bbl,
        b.bbl AS adjacent_bbl,
        CASE
            WHEN b.landmark_status IS NOT NULL THEN 'LANDMARK_74_79'
            ELSE 'ZLM'
        END AS transfer_type,
        CASE
            WHEN GREATEST(COALESCE(b.resid_far,0), COALESCE(b.comm_far,0)) > 0 AND b.lot_area_sf > 0
            THEN (GREATEST(b.resid_far, b.comm_far) - COALESCE(b.built_far, 0)) * b.lot_area_sf
            ELSE 0
        END AS available_sf
    FROM tax_lots a
    JOIN tax_lots b ON ST_Touches(a.geom, b.geom)
    WHERE a.bbl != b.bbl
      AND a.valid_to IS NULL
      AND b.valid_to IS NULL
)
SELECT
    target_bbl,
    COUNT(*) AS adjacent_count,
    ROUND(SUM(CASE WHEN transfer_type = 'ZLM' THEN available_sf ELSE 0 END), 0) AS zlm_available_sf,
    ROUND(SUM(CASE WHEN transfer_type = 'LANDMARK_74_79' THEN available_sf ELSE 0 END), 0) AS landmark_available_sf,
    ROUND(SUM(available_sf), 0) AS total_tdr_available_sf,
    ARRAY_AGG(DISTINCT adjacent_bbl) AS adjacent_bbls
FROM adjacent_lots
WHERE available_sf > 0
GROUP BY target_bbl;

CREATE UNIQUE INDEX idx_tdr_potential_bbl ON tdr_potential_by_lot(target_bbl);
CREATE INDEX idx_tdr_potential_total ON tdr_potential_by_lot(total_tdr_available_sf DESC);

-------------------------------------------------------------------------------
-- 8.3 Refresh Functions
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY lots_enriched;
    REFRESH MATERIALIZED VIEW CONCURRENTLY tdr_potential_by_lot;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SECTION 9: TRIGGERS FOR AUTO-TIMESTAMPS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'updated_at'
          AND table_schema = 'public'
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%I_updated_at ON %I;
            CREATE TRIGGER update_%I_updated_at
                BEFORE UPDATE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at();
        ', t, t, t, t);
    END LOOP;
END;
$$;

-- ============================================================================
-- SECTION 10: ROW-LEVEL SECURITY (Optional, for Phase 1+)
-- ============================================================================

-- Enable RLS on sensitive tables (commented out for Phase 0)
-- ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE tdr_scenarios ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE spatial_comments ENABLE ROW LEVEL SECURITY;

-- Example policies (uncomment when auth is added):
-- CREATE POLICY projects_workspace_access ON projects
--     FOR ALL
--     USING (
--         workspace_id IN (
--             SELECT workspace_id FROM workspace_members
--             WHERE user_id = current_setting('app.current_user_id')::UUID
--         )
--     );

-- ============================================================================
-- DONE
-- ============================================================================

COMMENT ON SCHEMA public IS 'DevSight NYC v1.0.0 - Initial schema with version control and collaboration';
