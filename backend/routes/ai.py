import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import ai as ai_module
import crud
import database
from models import User
from routes.board import require_user

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Board state sent by the frontend ---

class ChatCardData(BaseModel):
    id: int
    title: str
    details: str


class ChatColumnData(BaseModel):
    id: int
    title: str
    cards: list[ChatCardData]


class ChatBoardData(BaseModel):
    columns: list[ChatColumnData]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    board: ChatBoardData


# --- AI response ---

class AiChatResponse(BaseModel):
    message: str
    board_updated: bool
    operations: list[dict] | None = None


# --- System prompt ---

_SYSTEM_PROMPT = """\
You are an AI assistant for a Kanban board app called Kanban Studio.
The current board state is provided below. You help users manage their board.

You MUST respond with a valid JSON object following this exact structure:
{
  "message": "<your conversational reply>",
  "operations": [<list of board operations, or null if none needed>]
}

Available board operations (use the exact column_id / card_id values from the board):
  {"op": "create_card",   "column_id": <int>, "title": "<str>", "details": "<str>"}
  {"op": "move_card",     "card_id": <int>, "column_id": <int>, "position": <int>}
  {"op": "edit_card",     "card_id": <int>, "title": "<str|null>", "details": "<str|null>"}
  {"op": "delete_card",   "card_id": <int>}
  {"op": "rename_column", "column_id": <int>, "title": "<str>"}

position is 0-based (0 = top of column).
Only include "operations" when modifying the board. For questions or analysis, set it to null.
"""


def _build_system_prompt(board: ChatBoardData) -> str:
    board_json = json.dumps(
        {
            "columns": [
                {
                    "id": col.id,
                    "title": col.title,
                    "cards": [
                        {"id": c.id, "title": c.title, "details": c.details}
                        for c in col.cards
                    ],
                }
                for col in board.columns
            ]
        },
        indent=2,
    )
    return f"{_SYSTEM_PROMPT}\nCurrent board:\n{board_json}"


async def _apply_operations(
    db: AsyncSession, operations: list[dict]
) -> int:
    """Apply operations and return the number that succeeded."""
    applied = 0
    for op in operations:
        kind = op.get("op")
        try:
            if kind == "create_card":
                await crud.add_card(db, op["column_id"], op["title"], op.get("details", ""))
            elif kind == "move_card":
                await crud.move_card(db, op["card_id"], op["column_id"], op["position"])
            elif kind == "edit_card":
                await crud.update_card(db, op["card_id"], op.get("title"), op.get("details"))
            elif kind == "delete_card":
                await crud.delete_card(db, op["card_id"])
            elif kind == "rename_column":
                await crud.rename_column(db, op["column_id"], op["title"])
            else:
                logger.warning("Unknown operation type: %s", kind)
                continue
            applied += 1
        except Exception as e:
            # Skip invalid operations — don't abort the whole request
            logger.warning("Failed to apply operation %s: %s", op, e)
    return applied


# --- Routes ---

@router.get("/api/ai/ping")
async def ai_ping(user: User = Depends(require_user)):
    try:
        api_key = ai_module.get_api_key()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        result = await ai_module.chat_completion(
            api_key,
            messages=[{"role": "user", "content": "What is 2+2? Reply with just the number."}],
        )
    except Exception as exc:
        logger.error("OpenRouter ping failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}")
    return {"result": result.strip()}


@router.post("/api/ai/chat", response_model=AiChatResponse)
async def ai_chat(
    body: ChatRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    try:
        api_key = ai_module.get_api_key()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    system_prompt = _build_system_prompt(body.board)
    messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m.role, "content": m.content} for m in body.messages
    ]

    try:
        raw = await ai_module.chat_completion(
            api_key,
            messages=messages,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        logger.error("OpenRouter request failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return AiChatResponse(message=raw, board_updated=False)

    ai_message = parsed.get("message", raw)
    operations: list[dict] = parsed.get("operations") or []

    board_updated = False
    if operations:
        applied = await _apply_operations(db, operations)
        if applied > 0:
            await db.commit()
            board_updated = True

    return AiChatResponse(
        message=ai_message,
        board_updated=board_updated,
        operations=operations if board_updated else None,
    )
