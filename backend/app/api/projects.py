"""Project endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db

router = APIRouter()


class ProjectCreate(BaseModel):
    """Create project request."""
    workspace_id: UUID
    name: str
    description: Optional[str] = None
    project_type: str = "analysis"


class ProjectUpdate(BaseModel):
    """Update project request."""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None


class ProjectResponse(BaseModel):
    """Project response."""
    id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str]
    project_type: str
    current_version_id: Optional[UUID]
    settings: dict
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class VersionCreate(BaseModel):
    """Create version request."""
    name: Optional[str] = None
    description: Optional[str] = None
    version_type: str = "manual"
    snapshot_data: dict = {}


class VersionResponse(BaseModel):
    """Version response."""
    id: UUID
    project_id: UUID
    version_number: int
    name: Optional[str]
    description: Optional[str]
    version_type: str
    snapshot_data: dict
    created_by: UUID
    created_at: datetime


class CommentCreate(BaseModel):
    """Create comment request."""
    anchor_type: str  # BBL, COORDINATES, VIEWPORT
    anchor_bbl: Optional[int] = None
    anchor_point: Optional[dict] = None  # {lng, lat}
    anchor_viewport: Optional[dict] = None
    parent_id: Optional[UUID] = None
    content: str
    mentioned_user_ids: Optional[List[UUID]] = None


class CommentResponse(BaseModel):
    """Comment response."""
    id: UUID
    project_id: UUID
    user_id: UUID
    user_name: Optional[str]
    user_color: Optional[str]
    anchor_type: str
    anchor_bbl: Optional[int]
    anchor_point: Optional[dict]
    parent_id: Optional[UUID]
    content: str
    is_resolved: bool
    created_at: datetime
    replies: Optional[List["CommentResponse"]] = None


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    workspace_id: Optional[UUID] = Query(None, description="Filter by workspace"),
    db: AsyncSession = Depends(get_db),
):
    """List projects, optionally filtered by workspace."""
    conditions = ["deleted_at IS NULL"]
    params = {}

    if workspace_id:
        conditions.append("workspace_id = :workspace_id")
        params["workspace_id"] = str(workspace_id)

    where_clause = " AND ".join(conditions)

    query = text(f"""
        SELECT
            id, workspace_id, name, description, project_type,
            current_version_id, settings, created_by, created_at, updated_at
        FROM projects
        WHERE {where_clause}
        ORDER BY updated_at DESC
    """)

    result = await db.execute(query, params)
    rows = result.mappings().all()

    return [ProjectResponse(**dict(row)) for row in rows]


@router.post("", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    user_id: UUID = Query(..., description="User ID creating the project"),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    query = text("""
        INSERT INTO projects (workspace_id, name, description, project_type, created_by, settings)
        VALUES (:workspace_id, :name, :description, :project_type, :created_by, '{}')
        RETURNING id, workspace_id, name, description, project_type,
                  current_version_id, settings, created_by, created_at, updated_at
    """)

    result = await db.execute(query, {
        "workspace_id": str(project.workspace_id),
        "name": project.name,
        "description": project.description,
        "project_type": project.project_type,
        "created_by": str(user_id),
    })
    await db.commit()

    row = result.mappings().first()
    return ProjectResponse(**dict(row))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get project by ID."""
    query = text("""
        SELECT
            id, workspace_id, name, description, project_type,
            current_version_id, settings, created_by, created_at, updated_at
        FROM projects
        WHERE id = :project_id AND deleted_at IS NULL
    """)

    result = await db.execute(query, {"project_id": str(project_id)})
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(**dict(row))


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    update: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update project."""
    updates = []
    params = {"project_id": str(project_id)}

    if update.name is not None:
        updates.append("name = :name")
        params["name"] = update.name

    if update.description is not None:
        updates.append("description = :description")
        params["description"] = update.description

    if update.settings is not None:
        updates.append("settings = :settings")
        params["settings"] = update.settings

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = NOW()")
    set_clause = ", ".join(updates)

    query = text(f"""
        UPDATE projects
        SET {set_clause}
        WHERE id = :project_id AND deleted_at IS NULL
        RETURNING id, workspace_id, name, description, project_type,
                  current_version_id, settings, created_by, created_at, updated_at
    """)

    result = await db.execute(query, params)
    await db.commit()

    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(**dict(row))


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete project."""
    query = text("""
        UPDATE projects
        SET deleted_at = NOW(), updated_at = NOW()
        WHERE id = :project_id AND deleted_at IS NULL
        RETURNING id
    """)

    result = await db.execute(query, {"project_id": str(project_id)})
    await db.commit()

    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project deleted", "id": str(project_id)}


# Version endpoints
@router.get("/{project_id}/versions", response_model=List[VersionResponse])
async def list_versions(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all versions of a project."""
    query = text("""
        SELECT
            id, project_id, version_number, name, description,
            version_type, snapshot_data, created_by, created_at
        FROM project_versions
        WHERE project_id = :project_id
        ORDER BY version_number DESC
    """)

    result = await db.execute(query, {"project_id": str(project_id)})
    rows = result.mappings().all()

    return [VersionResponse(**dict(row)) for row in rows]


@router.post("/{project_id}/versions", response_model=VersionResponse)
async def create_version(
    project_id: UUID,
    version: VersionCreate,
    user_id: UUID = Query(..., description="User ID creating the version"),
    db: AsyncSession = Depends(get_db),
):
    """Create a new version snapshot."""
    query = text("""
        SELECT create_project_version(
            :project_id::uuid,
            :user_id::uuid,
            :name,
            :description,
            :version_type,
            :snapshot_data::jsonb
        ) AS version_id
    """)

    result = await db.execute(query, {
        "project_id": str(project_id),
        "user_id": str(user_id),
        "name": version.name,
        "description": version.description,
        "version_type": version.version_type,
        "snapshot_data": version.snapshot_data,
    })
    await db.commit()

    version_id = result.scalar()

    # Fetch the created version
    fetch_query = text("""
        SELECT
            id, project_id, version_number, name, description,
            version_type, snapshot_data, created_by, created_at
        FROM project_versions
        WHERE id = :version_id
    """)

    result = await db.execute(fetch_query, {"version_id": str(version_id)})
    row = result.mappings().first()

    return VersionResponse(**dict(row))


@router.post("/{project_id}/restore", response_model=VersionResponse)
async def restore_version(
    project_id: UUID,
    version_id: UUID = Query(..., description="Version ID to restore"),
    user_id: UUID = Query(..., description="User ID performing the restore"),
    db: AsyncSession = Depends(get_db),
):
    """Restore project to a previous version."""
    query = text("""
        SELECT restore_project_to_version(
            :project_id::uuid,
            :version_id::uuid,
            :user_id::uuid
        ) AS new_version_id
    """)

    try:
        result = await db.execute(query, {
            "project_id": str(project_id),
            "version_id": str(version_id),
            "user_id": str(user_id),
        })
        await db.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_version_id = result.scalar()

    # Fetch the created version
    fetch_query = text("""
        SELECT
            id, project_id, version_number, name, description,
            version_type, snapshot_data, created_by, created_at
        FROM project_versions
        WHERE id = :version_id
    """)

    result = await db.execute(fetch_query, {"version_id": str(new_version_id)})
    row = result.mappings().first()

    return VersionResponse(**dict(row))


# Comment endpoints
@router.get("/{project_id}/comments", response_model=List[CommentResponse])
async def list_comments(
    project_id: UUID,
    include_resolved: bool = Query(False, description="Include resolved comments"),
    db: AsyncSession = Depends(get_db),
):
    """List comments for a project."""
    conditions = ["sc.project_id = :project_id", "sc.deleted_at IS NULL", "sc.parent_id IS NULL"]

    if not include_resolved:
        conditions.append("sc.is_resolved = FALSE")

    where_clause = " AND ".join(conditions)

    # Get parent comments
    query = text(f"""
        SELECT
            sc.id, sc.project_id, sc.user_id, u.name AS user_name, u.display_color AS user_color,
            sc.anchor_type, sc.anchor_bbl,
            ST_AsGeoJSON(sc.anchor_point)::jsonb AS anchor_point,
            sc.parent_id, sc.content, sc.is_resolved, sc.created_at
        FROM spatial_comments sc
        LEFT JOIN users u ON u.id = sc.user_id
        WHERE {where_clause}
        ORDER BY sc.created_at DESC
    """)

    result = await db.execute(query, {"project_id": str(project_id)})
    parent_rows = result.mappings().all()

    comments = []
    for parent_row in parent_rows:
        comment = CommentResponse(**dict(parent_row), replies=[])

        # Get replies
        replies_query = text("""
            SELECT
                sc.id, sc.project_id, sc.user_id, u.name AS user_name, u.display_color AS user_color,
                sc.anchor_type, sc.anchor_bbl,
                ST_AsGeoJSON(sc.anchor_point)::jsonb AS anchor_point,
                sc.parent_id, sc.content, sc.is_resolved, sc.created_at
            FROM spatial_comments sc
            LEFT JOIN users u ON u.id = sc.user_id
            WHERE sc.parent_id = :parent_id AND sc.deleted_at IS NULL
            ORDER BY sc.created_at ASC
        """)

        replies_result = await db.execute(replies_query, {"parent_id": str(parent_row["id"])})
        comment.replies = [CommentResponse(**dict(r)) for r in replies_result.mappings()]

        comments.append(comment)

    return comments


@router.post("/{project_id}/comments", response_model=CommentResponse)
async def create_comment(
    project_id: UUID,
    comment: CommentCreate,
    user_id: UUID = Query(..., description="User ID creating the comment"),
    db: AsyncSession = Depends(get_db),
):
    """Create a new spatial comment."""
    # Build anchor point geometry if provided
    anchor_point_sql = "NULL"
    params = {
        "project_id": str(project_id),
        "user_id": str(user_id),
        "anchor_type": comment.anchor_type,
        "anchor_bbl": comment.anchor_bbl,
        "anchor_viewport": comment.anchor_viewport,
        "parent_id": str(comment.parent_id) if comment.parent_id else None,
        "content": comment.content,
        "mentioned_user_ids": [str(uid) for uid in comment.mentioned_user_ids] if comment.mentioned_user_ids else None,
    }

    if comment.anchor_point:
        anchor_point_sql = "ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)"
        params["lng"] = comment.anchor_point.get("lng")
        params["lat"] = comment.anchor_point.get("lat")

    query = text(f"""
        INSERT INTO spatial_comments (
            project_id, user_id, anchor_type, anchor_bbl, anchor_point,
            anchor_viewport, parent_id, content, mentioned_user_ids
        )
        VALUES (
            :project_id::uuid, :user_id::uuid, :anchor_type, :anchor_bbl,
            {anchor_point_sql}, :anchor_viewport, :parent_id::uuid, :content, :mentioned_user_ids
        )
        RETURNING id, project_id, user_id, anchor_type, anchor_bbl,
                  ST_AsGeoJSON(anchor_point)::jsonb AS anchor_point,
                  parent_id, content, is_resolved, created_at
    """)

    try:
        result = await db.execute(query, params)
        await db.commit()
    except Exception as e:
        if "Max 2 levels" in str(e):
            raise HTTPException(status_code=400, detail="Cannot reply to a reply. Max 2 levels allowed.")
        raise

    row = result.mappings().first()

    # Get user info
    user_query = text("SELECT name AS user_name, display_color AS user_color FROM users WHERE id = :user_id")
    user_result = await db.execute(user_query, {"user_id": str(user_id)})
    user_row = user_result.mappings().first()

    return CommentResponse(
        **dict(row),
        user_name=user_row["user_name"] if user_row else None,
        user_color=user_row["user_color"] if user_row else None,
    )
