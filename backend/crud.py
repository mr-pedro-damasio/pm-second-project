import bcrypt
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import ActivityEntry, Board, Card, KanbanColumn, User

DEFAULT_COLUMNS = ["Backlog", "Discovery", "In Progress", "Review", "Done"]

DEFAULT_CARDS: list[tuple[int, str, str]] = [
    (0, "Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
    (0, "Gather customer signals", "Review support tags, sales notes, and churn feedback."),
    (1, "Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
    (2, "Refine status language", "Standardize column labels and tone across the board."),
    (2, "Design card layout", "Add hierarchy and spacing for scanning dense lists."),
    (3, "QA micro-interactions", "Verify hover, focus, and loading states."),
    (4, "Ship marketing page", "Final copy approved and asset pack delivered."),
    (4, "Close onboarding sprint", "Document release notes and share internally."),
]


# --- Password helpers ---

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# --- User CRUD ---

async def get_user(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, username: str, password: str) -> User:
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def seed_default_user(db: AsyncSession) -> None:
    user = await get_user(db, "user")
    if user is None:
        user = User(username="user", password_hash=hash_password("password"))
        db.add(user)
        await db.flush()
    elif not user.password_hash:
        # Migrate existing user without password_hash
        user.password_hash = hash_password("password")
        await db.flush()

    board = await db.execute(select(Board).where(Board.user_id == user.id))
    if board.scalar_one_or_none() is None:
        new_board = Board(user_id=user.id, title="My Board")
        db.add(new_board)
        await db.flush()
        columns = []
        for i, title in enumerate(DEFAULT_COLUMNS):
            col = KanbanColumn(board_id=new_board.id, title=title, position=i)
            db.add(col)
            columns.append(col)
        await db.flush()
        col_position: dict[int, int] = {}
        for col_idx, card_title, card_details in DEFAULT_CARDS:
            pos = col_position.get(col_idx, 0)
            db.add(Card(column_id=columns[col_idx].id, title=card_title, details=card_details, position=pos))
            col_position[col_idx] = pos + 1

    await db.commit()


# --- Board CRUD ---

async def list_boards(db: AsyncSession, user_id: int) -> list[Board]:
    result = await db.execute(
        select(Board).where(Board.user_id == user_id).order_by(Board.id)
    )
    return list(result.scalars().all())


async def get_board(db: AsyncSession, board_id: int, user_id: int) -> Board | None:
    result = await db.execute(
        select(Board)
        .where(Board.id == board_id, Board.user_id == user_id)
        .options(selectinload(Board.columns).selectinload(KanbanColumn.cards))
    )
    return result.scalar_one_or_none()


async def get_first_board(db: AsyncSession, user: User) -> Board:
    result = await db.execute(
        select(Board)
        .where(Board.user_id == user.id)
        .options(selectinload(Board.columns).selectinload(KanbanColumn.cards))
        .order_by(Board.id)
    )
    return result.scalars().first()


async def create_board(db: AsyncSession, user_id: int, title: str) -> Board:
    board = Board(user_id=user_id, title=title)
    db.add(board)
    await db.flush()
    for i, col_title in enumerate(DEFAULT_COLUMNS):
        db.add(KanbanColumn(board_id=board.id, title=col_title, position=i))
    await db.flush()
    await db.refresh(board)
    return board


async def rename_board(db: AsyncSession, board_id: int, user_id: int, title: str) -> Board | None:
    result = await db.execute(
        select(Board).where(Board.id == board_id, Board.user_id == user_id)
    )
    board = result.scalar_one_or_none()
    if board is None:
        return None
    board.title = title
    await db.flush()
    return board


async def delete_board(db: AsyncSession, board_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(Board).where(Board.id == board_id, Board.user_id == user_id)
    )
    board = result.scalar_one_or_none()
    if board is None:
        return False
    await db.delete(board)
    await db.flush()
    return True


async def user_owns_column(db: AsyncSession, column_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(KanbanColumn.id)
        .join(Board)
        .where(KanbanColumn.id == column_id, Board.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


async def user_owns_card(db: AsyncSession, card_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(Card.id)
        .join(KanbanColumn)
        .join(Board)
        .where(Card.id == card_id, Board.user_id == user_id)
    )
    return result.scalar_one_or_none() is not None


# --- Column CRUD ---

async def _get_column_cards(
    db: AsyncSession, column_id: int, exclude_id: int | None = None
) -> list[Card]:
    q = select(Card).where(Card.column_id == column_id).order_by(Card.position)
    if exclude_id is not None:
        q = q.where(Card.id != exclude_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def rename_column(
    db: AsyncSession, column_id: int, title: str
) -> KanbanColumn | None:
    result = await db.execute(
        select(KanbanColumn).where(KanbanColumn.id == column_id)
    )
    col = result.scalar_one_or_none()
    if col is None:
        return None
    col.title = title
    await db.flush()
    return col


async def add_column(db: AsyncSession, board_id: int, title: str) -> KanbanColumn:
    result = await db.execute(
        select(KanbanColumn)
        .where(KanbanColumn.board_id == board_id)
        .order_by(KanbanColumn.position.desc())
    )
    last = result.scalars().first()
    position = (last.position + 1) if last else 0
    col = KanbanColumn(board_id=board_id, title=title, position=position)
    db.add(col)
    await db.flush()
    await db.refresh(col)
    return col


async def delete_column(db: AsyncSession, column_id: int) -> bool:
    result = await db.execute(
        select(KanbanColumn).where(KanbanColumn.id == column_id)
    )
    col = result.scalar_one_or_none()
    if col is None:
        return False
    await db.delete(col)
    await db.flush()
    return True


# --- Card CRUD ---

async def add_card(
    db: AsyncSession,
    column_id: int,
    title: str,
    details: str,
    priority: str = "medium",
    due_date: str | None = None,
    labels: list[str] | None = None,
) -> Card:
    cards = await _get_column_cards(db, column_id)
    position = len(cards)
    card = Card(
        column_id=column_id,
        title=title,
        details=details,
        priority=priority,
        due_date=due_date,
        labels=json.dumps(labels or []),
        position=position,
    )
    db.add(card)
    await db.flush()
    await db.refresh(card)
    return card


async def update_card(
    db: AsyncSession,
    card_id: int,
    title: str | None,
    details: str | None,
    priority: str | None = None,
    due_date: str | None = None,
    labels: list[str] | None = None,
) -> Card | None:
    result = await db.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if card is None:
        return None
    if title is not None:
        card.title = title
    if details is not None:
        card.details = details
    if priority is not None:
        card.priority = priority
    if due_date is not None:
        # Empty string signals "clear the due date"
        card.due_date = None if due_date == "" else due_date
    if labels is not None:
        card.labels = json.dumps(labels)
    await db.flush()
    return card


# --- Activity log ---

async def log_activity(db: AsyncSession, board_id: int, action: str, detail: str = "") -> None:
    entry = ActivityEntry(board_id=board_id, action=action, detail=detail)
    db.add(entry)
    await db.flush()


async def get_board_activity(db: AsyncSession, board_id: int, limit: int = 50) -> list[ActivityEntry]:
    result = await db.execute(
        select(ActivityEntry)
        .where(ActivityEntry.board_id == board_id)
        .order_by(ActivityEntry.id.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def delete_card(db: AsyncSession, card_id: int) -> bool:
    result = await db.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if card is None:
        return False
    await db.delete(card)
    await db.flush()
    return True


async def move_card(
    db: AsyncSession, card_id: int, to_column_id: int, to_position: int
) -> Card | None:
    result = await db.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if card is None:
        return None

    from_column_id = card.column_id

    if from_column_id == to_column_id:
        cards = await _get_column_cards(db, from_column_id, exclude_id=card_id)
        to_position = max(0, min(to_position, len(cards)))
        cards.insert(to_position, card)
        for i, c in enumerate(cards):
            c.position = i
    else:
        src_cards = await _get_column_cards(db, from_column_id, exclude_id=card_id)
        for i, c in enumerate(src_cards):
            c.position = i

        dst_cards = await _get_column_cards(db, to_column_id)
        to_position = max(0, min(to_position, len(dst_cards)))
        card.column_id = to_column_id
        dst_cards.insert(to_position, card)
        for i, c in enumerate(dst_cards):
            c.position = i

    await db.flush()
    return card
