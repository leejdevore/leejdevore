"""Tax lot endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db

router = APIRouter()


class LotSummary(BaseModel):
    """Summary of a tax lot for list views."""
    id: str
    bbl: int
    address: Optional[str]
    borough: str
    zoning_dist_1: Optional[str]
    lot_area_sf: Optional[float]
    bldg_area_sf: Optional[float]
    built_far: Optional[float]
    max_far: Optional[float]
    built_far_pct: Optional[float]
    unbuilt_sf: Optional[float]
    opportunity_score: Optional[float]


class LotDetail(BaseModel):
    """Detailed tax lot information."""
    id: str
    bbl: int
    borough: str
    block: int
    lot: int
    address: Optional[str]
    zip_code: Optional[str]

    # Zoning
    zoning_dist_1: Optional[str]
    zoning_dist_2: Optional[str]
    special_district_1: Optional[str]
    overlay_1: Optional[str]

    # FAR
    resid_far: Optional[float]
    comm_far: Optional[float]
    facil_far: Optional[float]
    built_far: Optional[float]
    max_far: Optional[float]
    built_far_pct: Optional[float]
    unbuilt_sf: Optional[float]

    # Building
    lot_area_sf: Optional[float]
    bldg_area_sf: Optional[float]
    num_floors: Optional[float]
    year_built: Optional[int]
    bldg_class: Optional[str]
    land_use: Optional[str]

    # Owner
    owner_name: Optional[str]
    owner_type: Optional[str]

    # Assessment
    assessed_land: Optional[float]
    assessed_total: Optional[float]

    # Landmark
    landmark_status: Optional[str]
    hist_dist: Optional[str]

    # Scores
    opportunity_score: Optional[float]
    distress_score: Optional[float]

    # Geometry as GeoJSON
    geom: Optional[dict]


class LotSearchParams(BaseModel):
    """Search parameters for lots."""
    built_far_pct_max: Optional[float] = None
    min_unbuilt_sf: Optional[float] = None
    zoning_districts: Optional[List[str]] = None
    boroughs: Optional[List[str]] = None
    min_lot_area: Optional[float] = None
    max_lot_area: Optional[float] = None
    exclude_landmarks: bool = True
    bbox: Optional[List[float]] = None  # [west, south, east, north]
    limit: int = 100
    offset: int = 0


class TDROpportunity(BaseModel):
    """TDR opportunity for a lot."""
    source_bbl: int
    source_address: Optional[str]
    transfer_type: str  # ZLM, LANDMARK_74_79, SPECIAL_DISTRICT
    available_sf: float
    is_adjacent: bool
    landmark_name: Optional[str] = None


@router.get("", response_model=List[LotSummary])
async def search_lots(
    built_far_pct_max: Optional[float] = Query(None, description="Max built FAR percentage"),
    min_unbuilt_sf: Optional[float] = Query(None, description="Minimum unbuilt square feet"),
    zoning_districts: Optional[str] = Query(None, description="Comma-separated zoning districts"),
    boroughs: Optional[str] = Query(None, description="Comma-separated boroughs (MN,BK,BX,QN,SI)"),
    min_lot_area: Optional[float] = Query(None, description="Minimum lot area SF"),
    max_lot_area: Optional[float] = Query(None, description="Maximum lot area SF"),
    exclude_landmarks: bool = Query(True, description="Exclude landmark sites"),
    bbox_west: Optional[float] = Query(None, description="Bounding box west"),
    bbox_south: Optional[float] = Query(None, description="Bounding box south"),
    bbox_east: Optional[float] = Query(None, description="Bounding box east"),
    bbox_north: Optional[float] = Query(None, description="Bounding box north"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Search tax lots with filters.

    Returns lots matching the specified criteria, ordered by opportunity score.
    """
    # Build dynamic query
    conditions = ["valid_to IS NULL"]
    params = {"limit": limit, "offset": offset}

    if built_far_pct_max is not None:
        conditions.append("""
            ROUND((built_far / NULLIF(GREATEST(resid_far, comm_far), 0)) * 100, 1) <= :built_far_pct_max
        """)
        params["built_far_pct_max"] = built_far_pct_max

    if min_unbuilt_sf is not None:
        conditions.append("""
            (GREATEST(resid_far, comm_far) - COALESCE(built_far, 0)) * lot_area_sf >= :min_unbuilt_sf
        """)
        params["min_unbuilt_sf"] = min_unbuilt_sf

    if zoning_districts:
        districts = [d.strip() for d in zoning_districts.split(",")]
        conditions.append("zoning_dist_1 = ANY(:zoning_districts)")
        params["zoning_districts"] = districts

    if boroughs:
        borough_list = [b.strip().upper() for b in boroughs.split(",")]
        conditions.append("borough = ANY(:boroughs)")
        params["boroughs"] = borough_list

    if min_lot_area is not None:
        conditions.append("lot_area_sf >= :min_lot_area")
        params["min_lot_area"] = min_lot_area

    if max_lot_area is not None:
        conditions.append("lot_area_sf <= :max_lot_area")
        params["max_lot_area"] = max_lot_area

    if exclude_landmarks:
        conditions.append("landmark_status IS NULL")

    if all([bbox_west, bbox_south, bbox_east, bbox_north]):
        conditions.append("""
            ST_Intersects(
                geom,
                ST_MakeEnvelope(:bbox_west, :bbox_south, :bbox_east, :bbox_north, 4326)
            )
        """)
        params["bbox_west"] = bbox_west
        params["bbox_south"] = bbox_south
        params["bbox_east"] = bbox_east
        params["bbox_north"] = bbox_north

    where_clause = " AND ".join(conditions)

    query = text(f"""
        SELECT
            tl.id::text,
            tl.bbl,
            tl.address,
            tl.borough,
            tl.zoning_dist_1,
            tl.lot_area_sf,
            tl.bldg_area_sf,
            tl.built_far,
            GREATEST(COALESCE(tl.resid_far, 0), COALESCE(tl.comm_far, 0)) AS max_far,
            ROUND((tl.built_far / NULLIF(GREATEST(tl.resid_far, tl.comm_far), 0)) * 100, 1) AS built_far_pct,
            ROUND((GREATEST(tl.resid_far, tl.comm_far) - COALESCE(tl.built_far, 0)) * tl.lot_area_sf, 0) AS unbuilt_sf,
            os.overall_score AS opportunity_score
        FROM tax_lots tl
        LEFT JOIN opportunity_scores os ON os.bbl = tl.bbl
        WHERE {where_clause}
        ORDER BY os.overall_score DESC NULLS LAST, unbuilt_sf DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(query, params)
    rows = result.mappings().all()

    return [LotSummary(**dict(row)) for row in rows]


@router.get("/{bbl}", response_model=LotDetail)
async def get_lot(
    bbl: int,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information for a specific tax lot."""
    query = text("""
        SELECT
            tl.id::text,
            tl.bbl,
            tl.borough,
            tl.block,
            tl.lot,
            tl.address,
            tl.zip_code,
            tl.zoning_dist_1,
            tl.zoning_dist_2,
            tl.special_district_1,
            tl.overlay_1,
            tl.resid_far,
            tl.comm_far,
            tl.facil_far,
            tl.built_far,
            GREATEST(COALESCE(tl.resid_far, 0), COALESCE(tl.comm_far, 0)) AS max_far,
            ROUND((tl.built_far / NULLIF(GREATEST(tl.resid_far, tl.comm_far), 0)) * 100, 1) AS built_far_pct,
            ROUND((GREATEST(tl.resid_far, tl.comm_far) - COALESCE(tl.built_far, 0)) * tl.lot_area_sf, 0) AS unbuilt_sf,
            tl.lot_area_sf,
            tl.bldg_area_sf,
            tl.num_floors,
            tl.year_built,
            tl.bldg_class,
            tl.land_use,
            tl.owner_name,
            tl.owner_type,
            tl.assessed_land,
            tl.assessed_total,
            tl.landmark_status,
            tl.hist_dist,
            os.overall_score AS opportunity_score,
            ll97.distress_score,
            ST_AsGeoJSON(tl.geom)::jsonb AS geom
        FROM tax_lots tl
        LEFT JOIN opportunity_scores os ON os.bbl = tl.bbl
        LEFT JOIN ll97_calculations ll97 ON ll97.bbl = tl.bbl
        WHERE tl.bbl = :bbl AND tl.valid_to IS NULL
    """)

    result = await db.execute(query, {"bbl": bbl})
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail=f"Lot {bbl} not found")

    return LotDetail(**dict(row))


@router.get("/{bbl}/tdr", response_model=List[TDROpportunity])
async def get_lot_tdr(
    bbl: int,
    include_landmarks: bool = Query(True, description="Include landmark TDR sources"),
    max_distance_ft: float = Query(500, description="Max distance for landmark search"),
    db: AsyncSession = Depends(get_db),
):
    """Get TDR opportunities for a target lot."""
    opportunities = []

    # ZLM - Adjacent lots with unused FAR
    zlm_query = text("""
        SELECT
            adjacent.bbl AS source_bbl,
            adjacent.address AS source_address,
            'ZLM' AS transfer_type,
            ROUND((GREATEST(adjacent.resid_far, adjacent.comm_far) - COALESCE(adjacent.built_far, 0)) * adjacent.lot_area_sf, 0) AS available_sf,
            TRUE AS is_adjacent
        FROM tax_lots target
        JOIN tax_lots adjacent ON ST_Touches(target.geom, adjacent.geom)
        WHERE target.bbl = :bbl
            AND target.valid_to IS NULL
            AND adjacent.valid_to IS NULL
            AND target.bbl != adjacent.bbl
            AND adjacent.landmark_status IS NULL
            AND (GREATEST(adjacent.resid_far, adjacent.comm_far) - COALESCE(adjacent.built_far, 0)) * adjacent.lot_area_sf > 0
        ORDER BY available_sf DESC
    """)

    result = await db.execute(zlm_query, {"bbl": bbl})
    for row in result.mappings():
        opportunities.append(TDROpportunity(**dict(row)))

    # Landmark 74-79 transfers
    if include_landmarks:
        landmark_query = text("""
            SELECT
                l.bbl AS source_bbl,
                tl.address AS source_address,
                'LANDMARK_74_79' AS transfer_type,
                COALESCE(l.unused_far * tl.lot_area_sf, 0) AS available_sf,
                ST_Touches(target.geom, tl.geom) AS is_adjacent,
                l.name AS landmark_name
            FROM tax_lots target
            JOIN landmarks l ON l.transfer_eligible = TRUE
            JOIN tax_lots tl ON tl.bbl = l.bbl AND tl.valid_to IS NULL
            WHERE target.bbl = :bbl
                AND target.valid_to IS NULL
                AND ST_DWithin(
                    target.geom::geography,
                    tl.geom::geography,
                    :max_distance_ft * 0.3048  -- Convert feet to meters
                )
                AND COALESCE(l.unused_far, 0) > 0
            ORDER BY available_sf DESC
        """)

        result = await db.execute(landmark_query, {"bbl": bbl, "max_distance_ft": max_distance_ft})
        for row in result.mappings():
            opportunities.append(TDROpportunity(**dict(row)))

    return opportunities


@router.get("/{bbl}/ll97")
async def get_lot_ll97(
    bbl: int,
    db: AsyncSession = Depends(get_db),
):
    """Get LL97 compliance information for a lot."""
    query = text("""
        SELECT
            ll97.*,
            ll84.site_eui,
            ll84.energy_star_score,
            ll84.total_ghg_emissions
        FROM ll97_calculations ll97
        LEFT JOIN ll84_energy_reports ll84 ON ll84.bbl = ll97.bbl
            AND ll84.report_year = (SELECT MAX(report_year) FROM ll84_energy_reports WHERE bbl = ll97.bbl)
        WHERE ll97.bbl = :bbl
    """)

    result = await db.execute(query, {"bbl": bbl})
    row = result.mappings().first()

    if not row:
        return {"bbl": bbl, "has_data": False, "message": "No LL97 data available for this lot"}

    return {
        "bbl": bbl,
        "has_data": True,
        **dict(row)
    }
