import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

import crud
import database
from models import User, KanbanColumn

router = APIRouter()


# --- Response models ---

class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    column_id: int
    title: str
    details: str
    priority: str
    due_date: str | None
    labels: list[str]
    position: int

    @field_validator("labels", mode="before")
    @classmethod
    def parse_labels(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                return []
        return v or []


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    detail: str


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


class BoardSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str


# --- Request models ---

class CreateBoardRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class RenameBoardRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


VALID_PRIORITIES = {"low", "medium", "high"}


class CreateCardRequest(BaseModel):
    column_id: int
    title: str = Field(..., min_length=1, max_length=200)
    details: str = Field(default="", max_length=2000)
    priority: str = Field(default="medium")
    due_date: str | None = Field(default=None)
    labels: list[str] = Field(default_factory=list)

    @property
    def validated_priority(self) -> str:
        return self.priority if self.priority in VALID_PRIORITIES else "medium"

    @property
    def validated_labels(self) -> list[str]:
        return [l.strip() for l in self.labels if l.strip()][:10]


class UpdateCardRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    details: str | None = Field(default=None, max_length=2000)
    priority: str | None = Field(default=None)
    due_date: str | None = Field(default=None)
    labels: list[str] | None = Field(default=None)

    @property
    def validated_priority(self) -> str | None:
        if self.priority is None:
            return None
        return self.priority if self.priority in VALID_PRIORITIES else "medium"

    @property
    def validated_labels(self) -> list[str] | None:
        if self.labels is None:
            return None
        return [l.strip() for l in self.labels if l.strip()][:10]


class CreateColumnRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class MoveCardRequest(BaseModel):
    column_id: int
    position: int


class RenameColumnRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


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

async def _assert_column_owned(db: AsyncSession, column_id: int, user_id: int) -> None:
    if not await crud.user_owns_column(db, column_id, user_id):
        raise HTTPException(status_code=404)


async def _assert_card_owned(db: AsyncSession, card_id: int, user_id: int) -> None:
    if not await crud.user_owns_card(db, card_id, user_id):
        raise HTTPException(status_code=404)


# --- Board routes ---

@router.get("/api/boards", response_model=list[BoardSummary])
async def list_boards(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    boards = await crud.list_boards(db, user.id)
    return [BoardSummary.model_validate(b) for b in boards]


@router.post("/api/boards", response_model=BoardOut, status_code=201)
async def create_board(
    body: CreateBoardRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board = await crud.create_board(db, user.id, body.title)
    await db.commit()
    board = await crud.get_board(db, board.id, user.id)
    return BoardOut.model_validate(board)


@router.get("/api/boards/{board_id}", response_model=BoardOut)
async def get_board(
    board_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board = await crud.get_board(db, board_id, user.id)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return BoardOut.model_validate(board)


@router.patch("/api/boards/{board_id}", response_model=BoardSummary)
async def rename_board(
    board_id: int,
    body: RenameBoardRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board = await crud.rename_board(db, board_id, user.id, body.title)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    await db.commit()
    return BoardSummary.model_validate(board)


@router.delete("/api/boards/{board_id}", status_code=204)
async def delete_board(
    board_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    # Prevent deleting the last board
    boards = await crud.list_boards(db, user.id)
    if len(boards) <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete your only board")
    deleted = await crud.delete_board(db, board_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Board not found")
    await db.commit()


# --- Legacy single-board route (first board) ---

@router.get("/api/board", response_model=BoardOut)
async def get_first_board(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board = await crud.get_first_board(db, user)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return BoardOut.model_validate(board)


# --- Board activity ---

@router.get("/api/boards/{board_id}/activity", response_model=list[ActivityOut])
async def get_board_activity(
    board_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board = await crud.get_board(db, board_id, user.id)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    entries = await crud.get_board_activity(db, board_id)
    return [ActivityOut.model_validate(e) for e in entries]


# --- Column management ---

@router.post("/api/boards/{board_id}/columns", response_model=ColumnOut, status_code=201)
async def create_column(
    board_id: int,
    body: CreateColumnRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    board = await crud.get_board(db, board_id, user.id)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    col = await crud.add_column(db, board_id, body.title)
    await crud.log_activity(db, board_id, "column_added", body.title)
    await db.commit()
    result = await db.execute(
        select(KanbanColumn)
        .where(KanbanColumn.id == col.id)
        .options(selectinload(KanbanColumn.cards))
    )
    return ColumnOut.model_validate(result.scalar_one())


@router.delete("/api/columns/{column_id}", status_code=204)
async def delete_column(
    column_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    if not await crud.user_owns_column(db, column_id, user.id):
        raise HTTPException(status_code=404)
    # Find board_id before deleting
    result = await db.execute(select(KanbanColumn).where(KanbanColumn.id == column_id))
    col = result.scalar_one_or_none()
    if col is None:
        raise HTTPException(status_code=404)
    board_id = col.board_id
    col_title = col.title
    # Count columns for this board — prevent deleting last column
    cols_result = await db.execute(
        select(KanbanColumn).where(KanbanColumn.board_id == board_id)
    )
    all_cols = list(cols_result.scalars().all())
    if len(all_cols) <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last column")
    deleted = await crud.delete_column(db, column_id)
    if not deleted:
        raise HTTPException(status_code=404)
    await crud.log_activity(db, board_id, "column_deleted", col_title)
    await db.commit()


# --- Card routes ---

@router.post("/api/cards", response_model=CardOut, status_code=201)
async def create_card(
    body: CreateCardRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    await _assert_column_owned(db, body.column_id, user.id)
    card = await crud.add_card(
        db, body.column_id, body.title, body.details,
        priority=body.validated_priority, due_date=body.due_date,
        labels=body.validated_labels,
    )
    # Find board_id for activity logging
    col_result = await db.execute(select(KanbanColumn).where(KanbanColumn.id == body.column_id))
    col = col_result.scalar_one_or_none()
    if col:
        await crud.log_activity(db, col.board_id, "card_created", body.title)
    await db.commit()
    return CardOut.model_validate(card)


@router.patch("/api/cards/{card_id}", response_model=CardOut)
async def update_card(
    card_id: int,
    body: UpdateCardRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    await _assert_card_owned(db, card_id, user.id)
    # Empty string means "clear due_date"; None means "don't change it"
    due_date_update = (
        "" if "due_date" in body.model_fields_set and body.due_date is None
        else body.due_date
    )
    card = await crud.update_card(
        db, card_id, body.title, body.details,
        priority=body.validated_priority,
        due_date=due_date_update,
        labels=body.validated_labels,
    )
    await db.commit()
    return CardOut.model_validate(card)


@router.delete("/api/cards/{card_id}", status_code=204)
async def delete_card(
    card_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    await _assert_card_owned(db, card_id, user.id)
    # Fetch card to get board_id for activity log
    from models import Card as CardModel
    card_result = await db.execute(
        select(CardModel).where(CardModel.id == card_id)
    )
    card_obj = card_result.scalar_one_or_none()
    board_id = None
    if card_obj:
        col_result = await db.execute(
            select(KanbanColumn).where(KanbanColumn.id == card_obj.column_id)
        )
        col = col_result.scalar_one_or_none()
        if col:
            board_id = col.board_id
    await crud.delete_card(db, card_id)
    if board_id:
        await crud.log_activity(db, board_id, "card_deleted", "")
    await db.commit()


@router.patch("/api/cards/{card_id}/move", response_model=CardOut)
async def move_card(
    card_id: int,
    body: MoveCardRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    await _assert_card_owned(db, card_id, user.id)
    await _assert_column_owned(db, body.column_id, user.id)
    card = await crud.move_card(db, card_id, body.column_id, body.position)
    # Find board_id for activity
    col_result = await db.execute(select(KanbanColumn).where(KanbanColumn.id == body.column_id))
    col = col_result.scalar_one_or_none()
    if col:
        await crud.log_activity(db, col.board_id, "card_moved", "")
    await db.commit()
    return CardOut.model_validate(card)


@router.patch("/api/columns/{column_id}", response_model=ColumnOut)
async def rename_column(
    column_id: int,
    body: RenameColumnRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(database.get_db),
):
    await _assert_column_owned(db, column_id, user.id)
    col = await crud.rename_column(db, column_id, body.title)
    await db.commit()
    result = await db.execute(
        select(KanbanColumn)
        .where(KanbanColumn.id == column_id)
        .options(selectinload(KanbanColumn.cards))
    )
    return ColumnOut.model_validate(result.scalar_one())
