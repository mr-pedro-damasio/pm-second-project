from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    boards: Mapped[list["Board"]] = relationship(back_populates="user")


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False, default="My Board")
    user: Mapped["User"] = relationship(back_populates="boards")
    columns: Mapped[list["KanbanColumn"]] = relationship(
        back_populates="board", order_by="KanbanColumn.position", cascade="all, delete-orphan"
    )
    activity: Mapped[list["ActivityEntry"]] = relationship(
        back_populates="board", order_by="ActivityEntry.id.desc()", cascade="all, delete-orphan"
    )


class KanbanColumn(Base):
    __tablename__ = "columns"
    __table_args__ = (Index("ix_columns_board_position", "board_id", "position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    board: Mapped["Board"] = relationship(back_populates="columns")
    cards: Mapped[list["Card"]] = relationship(
        back_populates="column", order_by="Card.position", cascade="all, delete-orphan"
    )


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = (Index("ix_cards_column_position", "column_id", "position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    column_id: Mapped[int] = mapped_column(ForeignKey("columns.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    priority: Mapped[str] = mapped_column(String, nullable=False, server_default="medium")
    due_date: Mapped[str | None] = mapped_column(String, nullable=True)
    labels: Mapped[str] = mapped_column(String, nullable=False, server_default="[]")
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    column: Mapped["KanbanColumn"] = relationship(back_populates="cards")


class ActivityEntry(Base):
    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    detail: Mapped[str] = mapped_column(String, nullable=False, server_default="")
    board: Mapped["Board"] = relationship(back_populates="activity")
