"""Workspace endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db

router = APIRouter()


class WorkspaceCreate(BaseModel):
    """Create workspace request."""
    name: str
    description: Optional[str] = None
    workspace_type: str = "team"


class WorkspaceUpdate(BaseModel):
    """Update workspace request."""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None


class WorkspaceResponse(BaseModel):
    """Workspace response."""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    workspace_type: str
    owner_id: Optional[UUID]
    settings: dict
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None


class MemberResponse(BaseModel):
    """Workspace member response."""
    id: UUID
    user_id: UUID
    user_name: Optional[str]
    user_email: Optional[str]
    user_color: Optional[str]
    role: str
    joined_at: datetime


class MemberInvite(BaseModel):
    """Invite member request."""
    user_id: UUID
    role: str = "member"


@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    user_id: UUID = Query(..., description="User ID to list workspaces for"),
    db: AsyncSession = Depends(get_db),
):
    """List workspaces for a user."""
    query = text("""
        SELECT
            w.id, w.name, w.slug, w.description, w.workspace_type,
            w.owner_id, w.settings, w.created_at, w.updated_at,
            COUNT(wm2.id) AS member_count
        FROM workspaces w
        JOIN workspace_members wm ON wm.workspace_id = w.id
        LEFT JOIN workspace_members wm2 ON wm2.workspace_id = w.id
        WHERE wm.user_id = :user_id AND w.deleted_at IS NULL
        GROUP BY w.id
        ORDER BY w.name
    """)

    result = await db.execute(query, {"user_id": str(user_id)})
    rows = result.mappings().all()

    return [WorkspaceResponse(**dict(row)) for row in rows]


@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    workspace: WorkspaceCreate,
    user_id: UUID = Query(..., description="User ID creating the workspace"),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workspace."""
    # Generate slug from name
    slug = workspace.name.lower().replace(" ", "-")

    # Check if slug exists
    check_query = text("SELECT id FROM workspaces WHERE slug = :slug")
    check_result = await db.execute(check_query, {"slug": slug})
    if check_result.scalar():
        # Append user id fragment to make unique
        slug = f"{slug}-{str(user_id)[:8]}"

    query = text("""
        INSERT INTO workspaces (name, slug, description, workspace_type, owner_id, settings)
        VALUES (:name, :slug, :description, :workspace_type, :owner_id::uuid, '{}')
        RETURNING id, name, slug, description, workspace_type, owner_id, settings, created_at, updated_at
    """)

    result = await db.execute(query, {
        "name": workspace.name,
        "slug": slug,
        "description": workspace.description,
        "workspace_type": workspace.workspace_type,
        "owner_id": str(user_id),
    })

    row = result.mappings().first()

    # Add owner as member
    member_query = text("""
        INSERT INTO workspace_members (workspace_id, user_id, role, joined_at)
        VALUES (:workspace_id::uuid, :user_id::uuid, 'owner', NOW())
    """)

    await db.execute(member_query, {
        "workspace_id": str(row["id"]),
        "user_id": str(user_id),
    })

    await db.commit()

    return WorkspaceResponse(**dict(row), member_count=1)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    user_id: UUID = Query(..., description="User ID requesting the workspace"),
    db: AsyncSession = Depends(get_db),
):
    """Get workspace by ID."""
    # Check membership
    member_query = text("""
        SELECT role FROM workspace_members
        WHERE workspace_id = :workspace_id AND user_id = :user_id
    """)
    member_result = await db.execute(member_query, {
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
    })

    if not member_result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    query = text("""
        SELECT
            w.id, w.name, w.slug, w.description, w.workspace_type,
            w.owner_id, w.settings, w.created_at, w.updated_at,
            COUNT(wm.id) AS member_count
        FROM workspaces w
        LEFT JOIN workspace_members wm ON wm.workspace_id = w.id
        WHERE w.id = :workspace_id AND w.deleted_at IS NULL
        GROUP BY w.id
    """)

    result = await db.execute(query, {"workspace_id": str(workspace_id)})
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return WorkspaceResponse(**dict(row))


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    update: WorkspaceUpdate,
    user_id: UUID = Query(..., description="User ID updating the workspace"),
    db: AsyncSession = Depends(get_db),
):
    """Update workspace."""
    # Check admin rights
    member_query = text("""
        SELECT role FROM workspace_members
        WHERE workspace_id = :workspace_id AND user_id = :user_id
    """)
    member_result = await db.execute(member_query, {
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
    })
    role = member_result.scalar()

    if role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Must be owner or admin to update workspace")

    updates = []
    params = {"workspace_id": str(workspace_id)}

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
        UPDATE workspaces
        SET {set_clause}
        WHERE id = :workspace_id AND deleted_at IS NULL
        RETURNING id, name, slug, description, workspace_type, owner_id, settings, created_at, updated_at
    """)

    result = await db.execute(query, params)
    await db.commit()

    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return WorkspaceResponse(**dict(row))


@router.get("/{workspace_id}/members", response_model=List[MemberResponse])
async def list_members(
    workspace_id: UUID,
    user_id: UUID = Query(..., description="User ID requesting members"),
    db: AsyncSession = Depends(get_db),
):
    """List workspace members."""
    # Check membership
    member_query = text("""
        SELECT role FROM workspace_members
        WHERE workspace_id = :workspace_id AND user_id = :user_id
    """)
    member_result = await db.execute(member_query, {
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
    })

    if not member_result.scalar():
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    query = text("""
        SELECT
            wm.id, wm.user_id, u.name AS user_name, u.email AS user_email,
            u.display_color AS user_color, wm.role, wm.joined_at
        FROM workspace_members wm
        JOIN users u ON u.id = wm.user_id
        WHERE wm.workspace_id = :workspace_id
        ORDER BY wm.joined_at
    """)

    result = await db.execute(query, {"workspace_id": str(workspace_id)})
    rows = result.mappings().all()

    return [MemberResponse(**dict(row)) for row in rows]


@router.post("/{workspace_id}/members", response_model=MemberResponse)
async def add_member(
    workspace_id: UUID,
    invite: MemberInvite,
    user_id: UUID = Query(..., description="User ID adding the member"),
    db: AsyncSession = Depends(get_db),
):
    """Add a member to the workspace."""
    # Check admin rights
    member_query = text("""
        SELECT role FROM workspace_members
        WHERE workspace_id = :workspace_id AND user_id = :user_id
    """)
    member_result = await db.execute(member_query, {
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
    })
    role = member_result.scalar()

    if role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Must be owner or admin to add members")

    # Check if already a member
    existing_query = text("""
        SELECT id FROM workspace_members
        WHERE workspace_id = :workspace_id AND user_id = :invite_user_id
    """)
    existing_result = await db.execute(existing_query, {
        "workspace_id": str(workspace_id),
        "invite_user_id": str(invite.user_id),
    })

    if existing_result.scalar():
        raise HTTPException(status_code=400, detail="User is already a member")

    # Add member
    query = text("""
        INSERT INTO workspace_members (workspace_id, user_id, role, invited_by, joined_at)
        VALUES (:workspace_id::uuid, :invite_user_id::uuid, :role, :invited_by::uuid, NOW())
        RETURNING id, user_id, role, joined_at
    """)

    result = await db.execute(query, {
        "workspace_id": str(workspace_id),
        "invite_user_id": str(invite.user_id),
        "role": invite.role,
        "invited_by": str(user_id),
    })
    await db.commit()

    row = result.mappings().first()

    # Get user info
    user_query = text("SELECT name AS user_name, email AS user_email, display_color AS user_color FROM users WHERE id = :user_id")
    user_result = await db.execute(user_query, {"user_id": str(invite.user_id)})
    user_row = user_result.mappings().first()

    return MemberResponse(
        **dict(row),
        user_name=user_row["user_name"] if user_row else None,
        user_email=user_row["user_email"] if user_row else None,
        user_color=user_row["user_color"] if user_row else None,
    )


@router.delete("/{workspace_id}/members/{member_user_id}")
async def remove_member(
    workspace_id: UUID,
    member_user_id: UUID,
    user_id: UUID = Query(..., description="User ID removing the member"),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the workspace."""
    # Check admin rights (or self-removal)
    member_query = text("""
        SELECT role FROM workspace_members
        WHERE workspace_id = :workspace_id AND user_id = :user_id
    """)
    member_result = await db.execute(member_query, {
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
    })
    role = member_result.scalar()

    if str(member_user_id) != str(user_id) and role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Must be owner or admin to remove members")

    # Cannot remove owner
    target_query = text("""
        SELECT role FROM workspace_members
        WHERE workspace_id = :workspace_id AND user_id = :member_user_id
    """)
    target_result = await db.execute(target_query, {
        "workspace_id": str(workspace_id),
        "member_user_id": str(member_user_id),
    })
    target_role = target_result.scalar()

    if target_role == "owner":
        raise HTTPException(status_code=400, detail="Cannot remove workspace owner")

    # Remove member
    query = text("""
        DELETE FROM workspace_members
        WHERE workspace_id = :workspace_id AND user_id = :member_user_id
        RETURNING id
    """)

    result = await db.execute(query, {
        "workspace_id": str(workspace_id),
        "member_user_id": str(member_user_id),
    })
    await db.commit()

    if not result.scalar():
        raise HTTPException(status_code=404, detail="Member not found")

    return {"message": "Member removed", "user_id": str(member_user_id)}


@router.post("/anonymous")
async def get_or_create_anonymous_user(
    anonymous_id: UUID = Query(..., description="Anonymous ID from client localStorage"),
    db: AsyncSession = Depends(get_db),
):
    """Get or create an anonymous user with personal workspace."""
    query = text("SELECT get_or_create_anonymous_user(:anonymous_id::uuid) AS user_id")

    result = await db.execute(query, {"anonymous_id": str(anonymous_id)})
    await db.commit()

    user_id = result.scalar()

    # Get user info
    user_query = text("""
        SELECT u.id, u.name, u.display_color, w.id AS workspace_id, w.slug AS workspace_slug
        FROM users u
        JOIN workspace_members wm ON wm.user_id = u.id
        JOIN workspaces w ON w.id = wm.workspace_id AND w.workspace_type = 'personal'
        WHERE u.id = :user_id
    """)

    user_result = await db.execute(user_query, {"user_id": str(user_id)})
    user_row = user_result.mappings().first()

    return {
        "user_id": str(user_row["id"]),
        "name": user_row["name"],
        "display_color": user_row["display_color"],
        "workspace_id": str(user_row["workspace_id"]),
        "workspace_slug": user_row["workspace_slug"],
    }
