from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

import crud
import database
from models import User

router = APIRouter()


# --- Response models ---

class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    column_id: int
    title: str
    details: str
    position: int


class ColumnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    position: int
    cards: list[CardOut]


class BoardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    columns: list[ColumnOut]


# --- Request models ---

class CreateCardRequest(BaseModel):
    column_id: int
    title: str
    details: str = ""


class UpdateCardRequest(BaseModel):
    title: str | None = None
    details: str | None = None


class MoveCardRequest(BaseModel):
    column_id: int
    position: int


class RenameColumnRequest(BaseModel):
    title: str


# --- Auth dependency ---

async def require_user(
    request: Request,
    db: AsyncSession = Depends(database.get_db),
) -> User:
    from main import _get_session  # avoid circular import at module level
    username = _get_session(request)
    if not username:
        raise HTTPException(status_code=401)
    user = await crud.get_user(db, username)
    if not user:
        raise HTTPException(status_code=401)
    return user


# --- Ownership helpers ---

async def _assert_column_owned(db: AsyncSession, column_id: int, board_id: int) -> None:
    from sqlalchemy import select
    from models import KanbanColumn
    result = await db.execute(
        select(KanbanColumn.id).where(
            KanbanColumn.id == column_id, KanbanColumn.board_id == board_id
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404)


async def _assert_card_owned(db: AsyncSession, card_id: int, board_id: int) -> None:
    from sqlalchemy import select
    from models import Card, KanbanColumn
    result = await db.execute(
        select(Card.id)
        .join(KanbanColumn)
        .where(Card.id == card_id, KanbanColumn.board_id == board_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404)


# --- Routes ---

@router.get("/api/board", response_model=BoardOut)
async def get_board(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board = await crud.get_board(db, user)
    return BoardOut.model_validate(board)


@router.post("/api/cards", response_model=CardOut, status_code=201)
async def create_card(
    body: CreateCardRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board_id = await crud.get_user_board_id(db, user.id)
    await _assert_column_owned(db, body.column_id, board_id)
    card = await crud.add_card(db, body.column_id, body.title, body.details)
    await db.commit()
    return CardOut.model_validate(card)


@router.patch("/api/cards/{card_id}", response_model=CardOut)
async def update_card(
    card_id: int,
    body: UpdateCardRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board_id = await crud.get_user_board_id(db, user.id)
    await _assert_card_owned(db, card_id, board_id)
    card = await crud.update_card(db, card_id, body.title, body.details)
    await db.commit()
    return CardOut.model_validate(card)


@router.delete("/api/cards/{card_id}", status_code=204)
async def delete_card(
    card_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board_id = await crud.get_user_board_id(db, user.id)
    await _assert_card_owned(db, card_id, board_id)
    await crud.delete_card(db, card_id)
    await db.commit()


@router.patch("/api/cards/{card_id}/move", response_model=CardOut)
async def move_card(
    card_id: int,
    body: MoveCardRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board_id = await crud.get_user_board_id(db, user.id)
    await _assert_card_owned(db, card_id, board_id)
    await _assert_column_owned(db, body.column_id, board_id)
    card = await crud.move_card(db, card_id, body.column_id, body.position)
    await db.commit()
    return CardOut.model_validate(card)


@router.patch("/api/columns/{column_id}", response_model=ColumnOut)
async def rename_column(
    column_id: int,
    body: RenameColumnRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board_id = await crud.get_user_board_id(db, user.id)
    await _assert_column_owned(db, column_id, board_id)
    col = await crud.rename_column(db, column_id, body.title)
    await db.commit()
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from models import KanbanColumn
    result = await db.execute(
        select(KanbanColumn)
        .where(KanbanColumn.id == column_id)
        .options(selectinload(KanbanColumn.cards))
    )
    return ColumnOut.model_validate(result.scalar_one())
