import { useEffect, useState } from "react";
import clsx from "clsx";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Card, Column, Priority } from "@/lib/kanban";
import { KanbanCard } from "@/components/KanbanCard";
import { NewCardForm } from "@/components/NewCardForm";

type KanbanColumnProps = {
  column: Column;
  cards: Card[];
  onRename: (columnId: string, title: string) => void;
  onAddCard: (columnId: string, title: string, details: string) => void;
  onDeleteCard: (columnId: string, cardId: string) => void;
  onEditCard: (cardId: string, fields: { title: string; details: string; priority: Priority; due_date: string | null; labels: string[] }) => void;
  onDeleteColumn: (columnId: string) => void;
  canDelete: boolean;
};

export const KanbanColumn = ({
  column,
  cards,
  onRename,
  onAddCard,
  onDeleteCard,
  onEditCard,
  onDeleteColumn,
  canDelete,
}: KanbanColumnProps) => {
  const { setNodeRef, isOver } = useDroppable({ id: column.id });
  const [localTitle, setLocalTitle] = useState(column.title);

  // Sync if parent reverts the title (e.g. on API error)
  useEffect(() => {
    setLocalTitle(column.title);
  }, [column.title]);

  return (
    <section
      ref={setNodeRef}
      className={clsx(
        "flex min-h-[520px] w-[260px] shrink-0 flex-col rounded-3xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-4 shadow-[var(--shadow)] transition",
        isOver && "ring-2 ring-[var(--accent-yellow)]"
      )}
      data-testid={`column-${column.id}`}
    >
      <div className="group/header flex items-center gap-2">
        <div className="h-5 w-1.5 shrink-0 rounded-full bg-[var(--accent-yellow)]" />
        <input
          value={localTitle}
          onChange={(e) => setLocalTitle(e.target.value)}
          onBlur={() => {
            if (localTitle.trim() === "") {
              setLocalTitle(column.title);
              return;
            }
            if (localTitle !== column.title) {
              onRename(column.id, localTitle);
            }
          }}
          className="min-w-0 flex-1 bg-transparent font-display text-sm font-semibold text-[var(--navy-dark)] outline-none"
          aria-label="Column title"
        />
        <span className="shrink-0 rounded-full bg-[var(--surface)] px-2 py-0.5 text-xs font-semibold text-[var(--gray-text)]">
          {cards.length}
        </span>
        {canDelete && (
          <button
            type="button"
            onClick={() => onDeleteColumn(column.id)}
            title="Delete column"
            className="shrink-0 rounded-md p-1 text-[var(--gray-text)] opacity-0 transition-opacity hover:text-red-400 group-hover/header:opacity-100"
            aria-label={`Delete column ${column.title}`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18" /><path d="M19 6l-1 14H6L5 6" /><path d="M8 6V4h8v2" />
            </svg>
          </button>
        )}
      </div>
      <div className="mt-4 flex flex-1 flex-col gap-3">
        <SortableContext items={column.cardIds} strategy={verticalListSortingStrategy}>
          {cards.map((card) => (
            <KanbanCard
              key={card.id}
              card={card}
              onDelete={(cardId) => onDeleteCard(column.id, cardId)}
              onEdit={onEditCard}
            />
          ))}
        </SortableContext>
        {cards.length === 0 && (
          <div className="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-[var(--stroke)] px-3 py-6 text-center text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Drop a card here
          </div>
        )}
      </div>
      <NewCardForm
        onAdd={(title, details) => onAddCard(column.id, title, details)}
      />
    </section>
  );
};
