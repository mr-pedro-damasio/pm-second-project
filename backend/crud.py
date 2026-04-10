from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Board, Card, KanbanColumn, User

DEFAULT_COLUMNS = ["Backlog", "Discovery", "In Progress", "Review", "Done"]


async def get_user(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def seed_default_user(db: AsyncSession) -> None:
    user = await get_user(db, "user")
    if user is None:
        user = User(username="user")
        db.add(user)
        await db.flush()

    board = await db.execute(select(Board).where(Board.user_id == user.id))
    if board.scalar_one_or_none() is None:
        new_board = Board(user_id=user.id, title="My Board")
        db.add(new_board)
        await db.flush()
        for i, title in enumerate(DEFAULT_COLUMNS):
            db.add(KanbanColumn(board_id=new_board.id, title=title, position=i))

    await db.commit()


async def get_board(db: AsyncSession, user: User) -> Board:
    result = await db.execute(
        select(Board)
        .where(Board.user_id == user.id)
        .options(selectinload(Board.columns).selectinload(KanbanColumn.cards))
    )
    return result.scalar_one()


async def get_user_board_id(db: AsyncSession, user_id: int) -> int | None:
    result = await db.execute(select(Board.id).where(Board.user_id == user_id))
    return result.scalar_one_or_none()


async def _get_column_cards(
    db: AsyncSession, column_id: int, exclude_id: int | None = None
) -> list[Card]:
    q = select(Card).where(Card.column_id == column_id).order_by(Card.position)
    if exclude_id is not None:
        q = q.where(Card.id != exclude_id)
    result = await db.execute(q)
    return list(result.scalars().all())


async def add_card(
    db: AsyncSession, column_id: int, title: str, details: str
) -> Card:
    cards = await _get_column_cards(db, column_id)
    position = len(cards)
    card = Card(column_id=column_id, title=title, details=details, position=position)
    db.add(card)
    await db.flush()
    await db.refresh(card)
    return card


async def update_card(
    db: AsyncSession, card_id: int, title: str | None, details: str | None
) -> Card | None:
    result = await db.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if card is None:
        return None
    if title is not None:
        card.title = title
    if details is not None:
        card.details = details
    await db.flush()
    return card


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
