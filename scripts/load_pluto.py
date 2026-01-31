#!/usr/bin/env python3
"""
Load PLUTO data into DevSight NYC database.

Usage:
    # From local shapefile
    python scripts/load_pluto.py --file MapPLUTO.shp

    # From local GeoJSON
    python scripts/load_pluto.py --file pluto.geojson

    # Download from NYC Open Data (MapPLUTO)
    python scripts/load_pluto.py --download

    # Specify PLUTO version (defaults to current date)
    python scripts/load_pluto.py --file MapPLUTO.shp --version 24v1
"""

import argparse
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text

# Default database URL (override with --db-url or DATABASE_URL env var)
DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/devsight"

# NYC Open Data MapPLUTO download URL (GeoJSON)
PLUTO_GEOJSON_URL = "https://data.cityofnewyork.us/api/geospatial/evjd-dqpz?method=export&format=GeoJSON"

# Column mapping: PLUTO name -> our schema name
COLUMN_MAP = {
    "bbl": "bbl",
    "borough": "borough",
    "block": "block",
    "lot": "lot",
    "address": "address",
    "zipcode": "zip_code",

    # Zoning
    "zonedist1": "zoning_dist_1",
    "zonedist2": "zoning_dist_2",
    "zonedist3": "zoning_dist_3",
    "zonedist4": "zoning_dist_4",
    "overlay1": "commercial_overlay_1",
    "overlay2": "commercial_overlay_2",
    "spdist1": "special_district_1",
    "spdist2": "special_district_2",
    "spdist3": "special_district_3",

    # FAR
    "residfar": "resid_far",
    "commfar": "comm_far",
    "facilfar": "facil_far",
    "builtfar": "built_far",

    # Building metrics
    "lotarea": "lot_area_sf",
    "bldgarea": "bldg_area_sf",
    "resarea": "res_area_sf",
    "officearea": "office_area_sf",
    "retailarea": "retail_area_sf",
    "numfloors": "num_floors",
    "numbldgs": "num_bldgs",
    "unitstotal": "num_units",
    "yearbuilt": "year_built",
    "yearalter1": "year_altered_1",
    "yearalter2": "year_altered_2",

    # Classification
    "bldgclass": "bldg_class",
    "landuse": "land_use",
    "ownertype": "owner_type",
    "ownername": "owner_name",

    # Landmark
    "landmark": "landmark_status",
    "histdist": "hist_district",

    # Assessment
    "assesstot": "assessed_total",
    "assessland": "assessed_land",
    "exempttot": "exempt_total",
}

# Borough code mapping
BOROUGH_CODES = {
    "1": "MN",
    "2": "BX",
    "3": "BK",
    "4": "QN",
    "5": "SI",
    "MN": "MN",
    "BX": "BX",
    "BK": "BK",
    "QN": "QN",
    "SI": "SI",
    "MANHATTAN": "MN",
    "BRONX": "BX",
    "BROOKLYN": "BK",
    "QUEENS": "QN",
    "STATEN ISLAND": "SI",
}


def download_pluto() -> gpd.GeoDataFrame:
    """Download PLUTO from NYC Open Data."""
    print(f"Downloading PLUTO from NYC Open Data...")
    print(f"URL: {PLUTO_GEOJSON_URL}")
    print("This may take a few minutes...")

    gdf = gpd.read_file(PLUTO_GEOJSON_URL)
    print(f"Downloaded {len(gdf):,} lots")
    return gdf


def load_from_file(file_path: str) -> gpd.GeoDataFrame:
    """Load PLUTO from local file."""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"Loading PLUTO from {file_path}...")
    gdf = gpd.read_file(file_path)
    print(f"Loaded {len(gdf):,} lots")
    return gdf


def normalize_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Normalize column names to lowercase for consistent mapping."""
    gdf.columns = gdf.columns.str.lower()
    return gdf


def map_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Map PLUTO columns to our schema."""
    # Keep only columns we need
    available = set(gdf.columns)
    rename_map = {k: v for k, v in COLUMN_MAP.items() if k in available}

    # Report missing columns
    missing = set(COLUMN_MAP.keys()) - available
    if missing:
        print(f"Note: {len(missing)} PLUTO columns not found (may vary by version):")
        print(f"  {', '.join(sorted(missing)[:10])}{'...' if len(missing) > 10 else ''}")

    # Select and rename
    cols_to_keep = list(rename_map.keys()) + ["geometry"]
    gdf = gdf[[c for c in cols_to_keep if c in gdf.columns]].copy()
    gdf = gdf.rename(columns=rename_map)

    return gdf


def normalize_borough(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Normalize borough codes to 2-letter format."""
    if "borough" in gdf.columns:
        gdf["borough"] = gdf["borough"].astype(str).str.upper().map(
            lambda x: BOROUGH_CODES.get(x, x[:2] if len(x) >= 2 else x)
        )
    return gdf


def ensure_multipolygon(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Convert all geometries to MultiPolygon for consistency."""
    from shapely.geometry import MultiPolygon, Polygon

    def to_multi(geom):
        if geom is None:
            return None
        if isinstance(geom, Polygon):
            return MultiPolygon([geom])
        return geom

    gdf["geometry"] = gdf["geometry"].apply(to_multi)
    return gdf


def add_versioning(gdf: gpd.GeoDataFrame, version: str) -> gpd.GeoDataFrame:
    """Add versioning columns."""
    gdf["pluto_version"] = version
    gdf["valid_from"] = date.today()
    gdf["valid_to"] = None
    return gdf


def clean_data(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Clean and validate data."""
    initial_count = len(gdf)

    # Remove rows without geometry
    gdf = gdf[gdf.geometry.notna()].copy()

    # Remove rows without BBL
    if "bbl" in gdf.columns:
        gdf = gdf[gdf["bbl"].notna()].copy()
        # Convert BBL to integer
        gdf["bbl"] = pd.to_numeric(gdf["bbl"], errors="coerce").astype("Int64")
        gdf = gdf[gdf["bbl"].notna()].copy()

    removed = initial_count - len(gdf)
    if removed > 0:
        print(f"Removed {removed:,} invalid rows (missing geometry or BBL)")

    # Ensure CRS is WGS84
    if gdf.crs is None:
        print("Warning: No CRS found, assuming EPSG:4326")
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs.to_epsg() != 4326:
        print(f"Converting CRS from {gdf.crs} to EPSG:4326")
        gdf = gdf.to_crs("EPSG:4326")

    return gdf


def load_to_database(gdf: gpd.GeoDataFrame, db_url: str, replace: bool = False):
    """Load GeoDataFrame into database."""
    print(f"Connecting to database...")
    engine = create_engine(db_url)

    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

    # Rename geometry column for PostGIS
    gdf = gdf.rename_geometry("geom")

    # Load to database
    if_exists = "replace" if replace else "append"
    print(f"Loading {len(gdf):,} lots to database (mode: {if_exists})...")

    gdf.to_postgis(
        "tax_lots",
        engine,
        if_exists=if_exists,
        index=False,
        dtype={"geom": "geometry"}
    )

    print("Data loaded successfully")
    return engine


def refresh_materialized_views(engine):
    """Refresh materialized views after data load."""
    print("Refreshing materialized views...")

    views = ["lots_enriched", "tdr_potential_by_lot"]

    with engine.connect() as conn:
        for view in views:
            try:
                print(f"  Refreshing {view}...")
                conn.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
                conn.commit()
                print(f"  {view} refreshed")
            except Exception as e:
                print(f"  Warning: Could not refresh {view}: {e}")
                print(f"  (This is normal if dependent tables are empty)")


def print_summary(engine):
    """Print summary of loaded data."""
    print("\n" + "=" * 50)
    print("LOAD SUMMARY")
    print("=" * 50)

    with engine.connect() as conn:
        # Total lots
        result = conn.execute(text("SELECT COUNT(*) FROM tax_lots"))
        total = result.scalar()
        print(f"Total lots: {total:,}")

        # By borough
        result = conn.execute(text("""
            SELECT borough, COUNT(*) as cnt
            FROM tax_lots
            GROUP BY borough
            ORDER BY borough
        """))
        print("\nBy borough:")
        for row in result:
            print(f"  {row[0]}: {row[1]:,}")

        # FAR stats
        result = conn.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE built_far < resid_far * 0.5) as underbuilt,
                COUNT(*) FILTER (WHERE resid_far > 0 OR comm_far > 0) as has_far
            FROM tax_lots
        """))
        row = result.fetchone()
        if row[1] > 0:
            print(f"\nLots with FAR data: {row[1]:,}")
            print(f"Underbuilt (<50% FAR): {row[0]:,}")


def main():
    parser = argparse.ArgumentParser(description="Load PLUTO data into DevSight NYC")
    parser.add_argument("--file", "-f", help="Path to PLUTO shapefile or GeoJSON")
    parser.add_argument("--download", "-d", action="store_true", help="Download from NYC Open Data")
    parser.add_argument("--version", "-v", default=None, help="PLUTO version (e.g., 24v1)")
    parser.add_argument("--db-url", default=None, help="Database URL")
    parser.add_argument("--replace", action="store_true", help="Replace existing data (default: append)")
    parser.add_argument("--skip-refresh", action="store_true", help="Skip refreshing materialized views")

    args = parser.parse_args()

    # Validate args
    if not args.file and not args.download:
        print("Error: Specify --file or --download")
        parser.print_help()
        sys.exit(1)

    # Get database URL
    import os
    db_url = args.db_url or os.environ.get("DATABASE_URL", DEFAULT_DB_URL)

    # Get version
    version = args.version or date.today().strftime("%yv1")

    # Load data
    if args.download:
        gdf = download_pluto()
    else:
        gdf = load_from_file(args.file)

    # Transform
    print("\nTransforming data...")
    gdf = normalize_columns(gdf)
    gdf = map_columns(gdf)
    gdf = normalize_borough(gdf)
    gdf = clean_data(gdf)
    gdf = ensure_multipolygon(gdf)
    gdf = add_versioning(gdf, version)

    print(f"Ready to load {len(gdf):,} lots (version: {version})")

    # Load to database
    engine = load_to_database(gdf, db_url, replace=args.replace)

    # Refresh views
    if not args.skip_refresh:
        refresh_materialized_views(engine)

    # Summary
    print_summary(engine)

    print("\nDone!")


if __name__ == "__main__":
    main()
