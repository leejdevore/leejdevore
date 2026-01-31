"""AI Chat endpoints using Claude API."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import json

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message."""
    role: str  # user, assistant
    content: str


class ChatRequest(BaseModel):
    """Chat request."""
    messages: List[ChatMessage]
    context: Optional[dict] = None  # Current viewport, selected lots, etc.
    stream: bool = False


class ActionProposal(BaseModel):
    """AI-proposed action."""
    action_type: str  # add_to_list, run_analysis, apply_filter, etc.
    label: str
    params: dict


class ChatResponse(BaseModel):
    """Chat response."""
    message: str
    actions: Optional[List[ActionProposal]] = None
    data: Optional[dict] = None  # Query results, analysis data


# System prompt for DevSight context
SYSTEM_PROMPT = """You are DevSight AI, an expert assistant for NYC real estate development analysis.

You help users:
1. Find development opportunities by analyzing lot FAR utilization
2. Calculate TDR (Transfer of Development Rights) potential
3. Assess LL97 compliance risks and distress opportunities
4. Understand zoning regulations and special districts
5. Analyze market trends by neighborhood

When responding:
- Be concise but informative
- Use NYC real estate terminology correctly
- Reference specific BBLs, addresses, or zoning when relevant
- Suggest actionable next steps when appropriate

You have access to the following data:
- MapPLUTO: Tax lot data including FAR, zoning, owner info
- LL84/LL97: Building energy and emissions data
- Landmarks: Protected sites and TDR source lots
- Market data: Rent trends, permit activity

Current context will be provided with each message, including the user's current viewport and any selected lots.
"""


@router.post("")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Process chat message and return AI response."""
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="AI chat is not configured. Set ANTHROPIC_API_KEY environment variable."
        )

    # Build context string
    context_str = ""
    if request.context:
        if request.context.get("viewport"):
            vp = request.context["viewport"]
            context_str += f"\nCurrent viewport: center [{vp.get('center', [])!r}], zoom {vp.get('zoom')}"

        if request.context.get("selected_bbls"):
            context_str += f"\nSelected lots: {request.context['selected_bbls']}"

        if request.context.get("active_filters"):
            context_str += f"\nActive filters: {json.dumps(request.context['active_filters'])}"

    # Check for data queries in the message
    last_message = request.messages[-1].content if request.messages else ""
    query_results = await _execute_data_queries(db, last_message, request.context)

    if query_results:
        context_str += f"\n\nQuery results:\n{json.dumps(query_results, indent=2, default=str)}"

    # Build messages for API
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Add context to last user message
    if context_str and messages:
        messages[-1]["content"] += f"\n\n[Context]{context_str}"

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        if request.stream:
            return StreamingResponse(
                _stream_response(client, messages),
                media_type="text/event-stream"
            )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        # Extract response text
        response_text = response.content[0].text if response.content else ""

        # Parse for action proposals
        actions = _extract_actions(response_text, query_results)

        return ChatResponse(
            message=response_text,
            actions=actions,
            data=query_results,
        )

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Anthropic SDK not installed. Run: pip install anthropic"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_response(client, messages):
    """Stream response from Claude API."""
    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {json.dumps({'text': text})}\n\n"

    yield "data: [DONE]\n\n"


async def _execute_data_queries(
    db: AsyncSession,
    message: str,
    context: Optional[dict]
) -> Optional[dict]:
    """Execute relevant data queries based on message content."""
    message_lower = message.lower()
    results = {}

    # Check for lot-specific queries
    if context and context.get("selected_bbls"):
        bbls = context["selected_bbls"]
        if len(bbls) <= 5:  # Limit for context
            query = text("""
                SELECT
                    bbl, address, zoning_dist_1,
                    built_far, GREATEST(resid_far, comm_far) AS max_far,
                    lot_area_sf, bldg_area_sf
                FROM tax_lots
                WHERE bbl = ANY(:bbls) AND valid_to IS NULL
            """)
            result = await db.execute(query, {"bbls": bbls})
            results["selected_lots"] = [dict(r) for r in result.mappings()]

    # Check for underbuilt lot queries
    if any(term in message_lower for term in ["underbuilt", "development potential", "low far", "opportunity"]):
        query = text("""
            SELECT
                bbl, address, zoning_dist_1,
                built_far, GREATEST(resid_far, comm_far) AS max_far,
                ROUND((built_far / NULLIF(GREATEST(resid_far, comm_far), 0)) * 100, 1) AS built_far_pct,
                ROUND((GREATEST(resid_far, comm_far) - COALESCE(built_far, 0)) * lot_area_sf, 0) AS unbuilt_sf
            FROM tax_lots
            WHERE valid_to IS NULL
                AND built_far < GREATEST(resid_far, comm_far) * 0.5
                AND landmark_status IS NULL
            ORDER BY unbuilt_sf DESC NULLS LAST
            LIMIT 5
        """)
        result = await db.execute(query)
        results["underbuilt_lots"] = [dict(r) for r in result.mappings()]

    # Check for LL97 queries
    if any(term in message_lower for term in ["ll97", "emissions", "penalty", "distress", "climate"]):
        query = text("""
            SELECT
                ll.bbl, tl.address, ll.building_type,
                ll.current_intensity, ll.threshold_2024, ll.threshold_2030,
                ll.compliant_2024, ll.compliant_2030,
                ll.penalty_2024, ll.penalty_2030, ll.distress_score
            FROM ll97_calculations ll
            JOIN tax_lots tl ON tl.bbl = ll.bbl AND tl.valid_to IS NULL
            WHERE ll.distress_score > 0.5
            ORDER BY ll.distress_score DESC
            LIMIT 5
        """)
        result = await db.execute(query)
        results["ll97_distressed"] = [dict(r) for r in result.mappings()]

    # Check for TDR queries
    if any(term in message_lower for term in ["tdr", "air rights", "transfer", "landmark"]):
        query = text("""
            SELECT
                l.name, l.landmark_type, l.bbl, tl.address,
                l.unused_far, tl.lot_area_sf,
                ROUND(l.unused_far * tl.lot_area_sf, 0) AS available_sf
            FROM landmarks l
            JOIN tax_lots tl ON tl.bbl = l.bbl AND tl.valid_to IS NULL
            WHERE l.transfer_eligible = TRUE AND COALESCE(l.unused_far, 0) > 0
            ORDER BY available_sf DESC NULLS LAST
            LIMIT 5
        """)
        result = await db.execute(query)
        results["tdr_sources"] = [dict(r) for r in result.mappings()]

    return results if results else None


def _extract_actions(response_text: str, query_results: Optional[dict]) -> Optional[List[ActionProposal]]:
    """Extract actionable proposals from response."""
    actions = []

    response_lower = response_text.lower()

    # Suggest adding lots to list
    if query_results and query_results.get("underbuilt_lots"):
        actions.append(ActionProposal(
            action_type="add_to_list",
            label="Add top opportunities to site list",
            params={"bbls": [lot["bbl"] for lot in query_results["underbuilt_lots"]]}
        ))

    # Suggest running TDR analysis
    if "tdr" in response_lower or "air rights" in response_lower:
        actions.append(ActionProposal(
            action_type="run_tdr_analysis",
            label="Run TDR analysis",
            params={}
        ))

    # Suggest applying filters
    if "filter" in response_lower or "narrow down" in response_lower:
        actions.append(ActionProposal(
            action_type="apply_filter",
            label="Apply suggested filters",
            params={}
        ))

    # Suggest LL97 deep dive
    if query_results and query_results.get("ll97_distressed"):
        actions.append(ActionProposal(
            action_type="view_ll97_details",
            label="View LL97 distress analysis",
            params={"bbls": [lot["bbl"] for lot in query_results["ll97_distressed"]]}
        ))

    return actions if actions else None
