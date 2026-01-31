"""TDR Scenario endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db

router = APIRouter()


class ScenarioCreate(BaseModel):
    """Create scenario request."""
    project_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    target_bbl: int
    scenario_type: str = "ZLM"


class ScenarioUpdate(BaseModel):
    """Update scenario request."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_public: Optional[bool] = None


class TDRSourceCreate(BaseModel):
    """Add TDR source to scenario."""
    source_bbl: int
    source_type: str
    proposed_transfer_sf: float
    estimated_price_psf: Optional[float] = None
    landmark_id: Optional[UUID] = None


class TDRSourceResponse(BaseModel):
    """TDR source response."""
    id: UUID
    source_bbl: int
    source_type: str
    lot_area_sf: Optional[float]
    available_sf: Optional[float]
    proposed_transfer_sf: float
    estimated_price_psf: Optional[float]
    estimated_total: Optional[float]
    is_adjacent: Optional[bool]
    landmark_name: Optional[str]


class ScenarioResponse(BaseModel):
    """Scenario response."""
    id: UUID
    project_id: Optional[UUID]
    created_by: UUID
    name: str
    description: Optional[str]
    target_bbl: int
    target_lot_area: Optional[float]
    target_current_far: Optional[float]
    target_max_far: Optional[float]
    target_absorbable_sf: Optional[float]
    scenario_type: str
    total_transferable_sf: Optional[float]
    estimated_cost: Optional[float]
    cost_per_sf: Optional[float]
    status: str
    is_public: bool
    created_at: datetime
    updated_at: datetime
    sources: Optional[List[TDRSourceResponse]] = None


class ShareCreate(BaseModel):
    """Share scenario request."""
    user_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    permission: str = "view"
    expires_at: Optional[datetime] = None


class ShareResponse(BaseModel):
    """Share response."""
    id: UUID
    scenario_id: UUID
    shared_with_user_id: Optional[UUID]
    shared_with_workspace_id: Optional[UUID]
    permission: str
    shared_by: UUID
    shared_at: datetime
    expires_at: Optional[datetime]


@router.get("", response_model=List[ScenarioResponse])
async def list_scenarios(
    user_id: UUID = Query(..., description="User ID to list scenarios for"),
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    include_shared: bool = Query(True, description="Include shared scenarios"),
    db: AsyncSession = Depends(get_db),
):
    """List scenarios for a user."""
    query = text("""
        WITH user_scenarios AS (
            -- Owned scenarios
            SELECT s.* FROM tdr_scenarios s
            WHERE s.created_by = :user_id
            UNION
            -- Shared scenarios
            SELECT s.* FROM tdr_scenarios s
            JOIN scenario_shares ss ON ss.scenario_id = s.id
            WHERE :include_shared
                AND (ss.shared_with_user_id = :user_id
                     OR ss.shared_with_workspace_id IN (
                         SELECT workspace_id FROM workspace_members WHERE user_id = :user_id
                     ))
                AND (ss.expires_at IS NULL OR ss.expires_at > NOW())
        )
        SELECT DISTINCT *
        FROM user_scenarios
        WHERE (:project_id IS NULL OR project_id = :project_id)
        ORDER BY updated_at DESC
    """)

    result = await db.execute(query, {
        "user_id": str(user_id),
        "project_id": str(project_id) if project_id else None,
        "include_shared": include_shared,
    })
    rows = result.mappings().all()

    return [ScenarioResponse(**dict(row)) for row in rows]


@router.post("", response_model=ScenarioResponse)
async def create_scenario(
    scenario: ScenarioCreate,
    user_id: UUID = Query(..., description="User ID creating the scenario"),
    db: AsyncSession = Depends(get_db),
):
    """Create a new TDR scenario."""
    # Get target lot info
    lot_query = text("""
        SELECT
            lot_area_sf AS target_lot_area,
            built_far AS target_current_far,
            GREATEST(COALESCE(resid_far, 0), COALESCE(comm_far, 0)) AS target_max_far,
            ROUND((GREATEST(resid_far, comm_far) - COALESCE(built_far, 0)) * lot_area_sf, 0) AS target_absorbable_sf
        FROM tax_lots
        WHERE bbl = :bbl AND valid_to IS NULL
    """)

    lot_result = await db.execute(lot_query, {"bbl": scenario.target_bbl})
    lot_info = lot_result.mappings().first()

    if not lot_info:
        raise HTTPException(status_code=404, detail=f"Target lot {scenario.target_bbl} not found")

    # Create scenario
    query = text("""
        INSERT INTO tdr_scenarios (
            project_id, created_by, name, description, target_bbl,
            target_lot_area, target_current_far, target_max_far, target_absorbable_sf,
            scenario_type, status
        )
        VALUES (
            :project_id::uuid, :created_by::uuid, :name, :description, :target_bbl,
            :target_lot_area, :target_current_far, :target_max_far, :target_absorbable_sf,
            :scenario_type, 'draft'
        )
        RETURNING *
    """)

    result = await db.execute(query, {
        "project_id": str(scenario.project_id) if scenario.project_id else None,
        "created_by": str(user_id),
        "name": scenario.name,
        "description": scenario.description,
        "target_bbl": scenario.target_bbl,
        "target_lot_area": lot_info["target_lot_area"],
        "target_current_far": lot_info["target_current_far"],
        "target_max_far": lot_info["target_max_far"],
        "target_absorbable_sf": lot_info["target_absorbable_sf"],
        "scenario_type": scenario.scenario_type,
    })
    await db.commit()

    row = result.mappings().first()
    return ScenarioResponse(**dict(row))


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: UUID,
    user_id: UUID = Query(..., description="User ID requesting the scenario"),
    db: AsyncSession = Depends(get_db),
):
    """Get scenario by ID with access check."""
    # Check access
    access_query = text("""
        SELECT EXISTS (
            SELECT 1 FROM tdr_scenarios s
            WHERE s.id = :scenario_id
                AND (
                    s.created_by = :user_id
                    OR s.is_public = TRUE
                    OR EXISTS (
                        SELECT 1 FROM scenario_shares ss
                        WHERE ss.scenario_id = s.id
                            AND (ss.shared_with_user_id = :user_id
                                 OR ss.shared_with_workspace_id IN (
                                     SELECT workspace_id FROM workspace_members WHERE user_id = :user_id
                                 ))
                            AND (ss.expires_at IS NULL OR ss.expires_at > NOW())
                    )
                )
        ) AS has_access
    """)

    access_result = await db.execute(access_query, {
        "scenario_id": str(scenario_id),
        "user_id": str(user_id),
    })

    if not access_result.scalar():
        raise HTTPException(status_code=403, detail="Access denied to this scenario")

    # Get scenario
    query = text("""
        SELECT * FROM tdr_scenarios WHERE id = :scenario_id
    """)

    result = await db.execute(query, {"scenario_id": str(scenario_id)})
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = ScenarioResponse(**dict(row))

    # Get sources
    sources_query = text("""
        SELECT
            ts.id, ts.source_bbl, ts.source_type, ts.lot_area_sf,
            ts.available_sf, ts.proposed_transfer_sf, ts.estimated_price_psf,
            ts.estimated_total, ts.is_adjacent, l.name AS landmark_name
        FROM tdr_sources ts
        LEFT JOIN landmarks l ON l.id = ts.landmark_id
        WHERE ts.scenario_id = :scenario_id
        ORDER BY ts.proposed_transfer_sf DESC
    """)

    sources_result = await db.execute(sources_query, {"scenario_id": str(scenario_id)})
    scenario.sources = [TDRSourceResponse(**dict(s)) for s in sources_result.mappings()]

    return scenario


@router.put("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: UUID,
    update: ScenarioUpdate,
    user_id: UUID = Query(..., description="User ID updating the scenario"),
    db: AsyncSession = Depends(get_db),
):
    """Update scenario."""
    # Check ownership
    owner_query = text("SELECT created_by FROM tdr_scenarios WHERE id = :scenario_id")
    owner_result = await db.execute(owner_query, {"scenario_id": str(scenario_id)})
    owner_row = owner_result.mappings().first()

    if not owner_row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    if str(owner_row["created_by"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Only the owner can update this scenario")

    updates = []
    params = {"scenario_id": str(scenario_id)}

    if update.name is not None:
        updates.append("name = :name")
        params["name"] = update.name

    if update.description is not None:
        updates.append("description = :description")
        params["description"] = update.description

    if update.status is not None:
        updates.append("status = :status")
        params["status"] = update.status

    if update.is_public is not None:
        updates.append("is_public = :is_public")
        params["is_public"] = update.is_public

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = NOW()")
    set_clause = ", ".join(updates)

    query = text(f"""
        UPDATE tdr_scenarios
        SET {set_clause}
        WHERE id = :scenario_id
        RETURNING *
    """)

    result = await db.execute(query, params)
    await db.commit()

    row = result.mappings().first()
    return ScenarioResponse(**dict(row))


@router.post("/{scenario_id}/sources", response_model=TDRSourceResponse)
async def add_tdr_source(
    scenario_id: UUID,
    source: TDRSourceCreate,
    user_id: UUID = Query(..., description="User ID adding the source"),
    db: AsyncSession = Depends(get_db),
):
    """Add a TDR source to a scenario."""
    # Check ownership
    owner_query = text("SELECT created_by, target_bbl FROM tdr_scenarios WHERE id = :scenario_id")
    owner_result = await db.execute(owner_query, {"scenario_id": str(scenario_id)})
    owner_row = owner_result.mappings().first()

    if not owner_row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    if str(owner_row["created_by"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Only the owner can modify this scenario")

    # Get source lot info
    lot_query = text("""
        SELECT
            lot_area_sf,
            built_far AS current_far,
            GREATEST(COALESCE(resid_far, 0), COALESCE(comm_far, 0)) AS max_far,
            ROUND((GREATEST(resid_far, comm_far) - COALESCE(built_far, 0)) * lot_area_sf, 0) AS available_sf,
            ST_Touches(
                (SELECT geom FROM tax_lots WHERE bbl = :target_bbl AND valid_to IS NULL),
                geom
            ) AS is_adjacent
        FROM tax_lots
        WHERE bbl = :source_bbl AND valid_to IS NULL
    """)

    lot_result = await db.execute(lot_query, {
        "source_bbl": source.source_bbl,
        "target_bbl": owner_row["target_bbl"],
    })
    lot_info = lot_result.mappings().first()

    if not lot_info:
        raise HTTPException(status_code=404, detail=f"Source lot {source.source_bbl} not found")

    # Calculate estimated total
    estimated_total = None
    if source.estimated_price_psf and source.proposed_transfer_sf:
        estimated_total = source.estimated_price_psf * source.proposed_transfer_sf

    # Insert source
    query = text("""
        INSERT INTO tdr_sources (
            scenario_id, source_bbl, source_type, lot_area_sf,
            current_far, max_far, available_sf, proposed_transfer_sf,
            estimated_price_psf, estimated_total, is_adjacent, landmark_id
        )
        VALUES (
            :scenario_id::uuid, :source_bbl, :source_type, :lot_area_sf,
            :current_far, :max_far, :available_sf, :proposed_transfer_sf,
            :estimated_price_psf, :estimated_total, :is_adjacent, :landmark_id::uuid
        )
        RETURNING *
    """)

    result = await db.execute(query, {
        "scenario_id": str(scenario_id),
        "source_bbl": source.source_bbl,
        "source_type": source.source_type,
        "lot_area_sf": lot_info["lot_area_sf"],
        "current_far": lot_info["current_far"],
        "max_far": lot_info["max_far"],
        "available_sf": lot_info["available_sf"],
        "proposed_transfer_sf": source.proposed_transfer_sf,
        "estimated_price_psf": source.estimated_price_psf,
        "estimated_total": estimated_total,
        "is_adjacent": lot_info["is_adjacent"],
        "landmark_id": str(source.landmark_id) if source.landmark_id else None,
    })
    await db.commit()

    # Update scenario totals
    await _update_scenario_totals(db, scenario_id)

    row = result.mappings().first()
    return TDRSourceResponse(**dict(row))


@router.post("/{scenario_id}/share", response_model=ShareResponse)
async def share_scenario(
    scenario_id: UUID,
    share: ShareCreate,
    user_id: UUID = Query(..., description="User ID sharing the scenario"),
    db: AsyncSession = Depends(get_db),
):
    """Share a scenario with a user or workspace."""
    if not share.user_id and not share.workspace_id:
        raise HTTPException(status_code=400, detail="Must specify user_id or workspace_id")

    if share.user_id and share.workspace_id:
        raise HTTPException(status_code=400, detail="Cannot specify both user_id and workspace_id")

    # Check ownership
    owner_query = text("SELECT created_by FROM tdr_scenarios WHERE id = :scenario_id")
    owner_result = await db.execute(owner_query, {"scenario_id": str(scenario_id)})
    owner_row = owner_result.mappings().first()

    if not owner_row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    if str(owner_row["created_by"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Only the owner can share this scenario")

    query = text("""
        INSERT INTO scenario_shares (
            scenario_id, shared_with_user_id, shared_with_workspace_id,
            permission, shared_by, expires_at
        )
        VALUES (
            :scenario_id::uuid, :shared_with_user_id::uuid, :shared_with_workspace_id::uuid,
            :permission, :shared_by::uuid, :expires_at
        )
        RETURNING *
    """)

    result = await db.execute(query, {
        "scenario_id": str(scenario_id),
        "shared_with_user_id": str(share.user_id) if share.user_id else None,
        "shared_with_workspace_id": str(share.workspace_id) if share.workspace_id else None,
        "permission": share.permission,
        "shared_by": str(user_id),
        "expires_at": share.expires_at,
    })
    await db.commit()

    row = result.mappings().first()
    return ShareResponse(**dict(row))


@router.delete("/{scenario_id}/share/{share_id}")
async def revoke_share(
    scenario_id: UUID,
    share_id: UUID,
    user_id: UUID = Query(..., description="User ID revoking the share"),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a scenario share."""
    # Check ownership
    owner_query = text("SELECT created_by FROM tdr_scenarios WHERE id = :scenario_id")
    owner_result = await db.execute(owner_query, {"scenario_id": str(scenario_id)})
    owner_row = owner_result.mappings().first()

    if not owner_row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    if str(owner_row["created_by"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Only the owner can revoke shares")

    query = text("""
        DELETE FROM scenario_shares
        WHERE id = :share_id AND scenario_id = :scenario_id
        RETURNING id
    """)

    result = await db.execute(query, {
        "share_id": str(share_id),
        "scenario_id": str(scenario_id),
    })
    await db.commit()

    if not result.scalar():
        raise HTTPException(status_code=404, detail="Share not found")

    return {"message": "Share revoked", "id": str(share_id)}


async def _update_scenario_totals(db: AsyncSession, scenario_id: UUID):
    """Update scenario totals from sources."""
    query = text("""
        UPDATE tdr_scenarios s
        SET
            total_transferable_sf = (
                SELECT COALESCE(SUM(proposed_transfer_sf), 0)
                FROM tdr_sources WHERE scenario_id = :scenario_id
            ),
            estimated_cost = (
                SELECT COALESCE(SUM(estimated_total), 0)
                FROM tdr_sources WHERE scenario_id = :scenario_id
            ),
            cost_per_sf = CASE
                WHEN (SELECT SUM(proposed_transfer_sf) FROM tdr_sources WHERE scenario_id = :scenario_id) > 0
                THEN (SELECT SUM(estimated_total) FROM tdr_sources WHERE scenario_id = :scenario_id)
                     / (SELECT SUM(proposed_transfer_sf) FROM tdr_sources WHERE scenario_id = :scenario_id)
                ELSE NULL
            END,
            updated_at = NOW()
        WHERE id = :scenario_id
    """)

    await db.execute(query, {"scenario_id": str(scenario_id)})
    await db.commit()
