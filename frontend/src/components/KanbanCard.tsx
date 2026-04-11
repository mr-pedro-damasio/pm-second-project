import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card, Priority } from "@/lib/kanban";
import { CardEditModal } from "@/components/CardEditModal";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => void;
  onEdit: (cardId: string, fields: { title: string; details: string; priority: Priority; due_date: string | null; labels: string[] }) => void;
};

const PRIORITY_STYLES: Record<Priority, string> = {
  low: "bg-emerald-100 text-emerald-700",
  medium: "bg-amber-100 text-amber-700",
  high: "bg-red-100 text-red-600",
};

function isOverdue(dueDate: string): boolean {
  return dueDate < new Date().toISOString().slice(0, 10);
}

export const KanbanCard = ({ card, onDelete, onEdit }: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });
  const [editing, setEditing] = useState(false);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const overdue = card.due_date ? isOverdue(card.due_date) : false;

  return (
    <>
      <article
        ref={setNodeRef}
        style={style}
        className={clsx(
          "group rounded-2xl border bg-white px-4 py-3.5 shadow-[0_12px_24px_rgba(3,33,71,0.08)]",
          "transition-all duration-150",
          isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]",
          overdue ? "border-red-200" : "border-transparent"
        )}
        {...attributes}
        {...listeners}
        data-testid={`card-${card.id}`}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h4 className="font-display text-sm font-semibold leading-5 text-[var(--navy-dark)]">
              {card.title}
            </h4>
            {card.details && (
              <p className="mt-1.5 line-clamp-2 text-xs leading-[1.6] text-[var(--gray-text)]">
                {card.details}
              </p>
            )}
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              {card.priority !== "medium" && (
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${PRIORITY_STYLES[card.priority]}`}>
                  {card.priority}
                </span>
              )}
              {card.due_date && (
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${overdue ? "bg-red-100 text-red-600" : "bg-[var(--surface)] text-[var(--gray-text)]"}`}>
                  {overdue ? "Overdue" : ""} {card.due_date}
                </span>
              )}
              {card.labels?.map((label) => (
                <span
                  key={label}
                  className="rounded-full bg-[#209dd7]/10 px-2 py-0.5 text-[10px] font-semibold text-[var(--primary-blue)]"
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
          <div className="flex shrink-0 flex-col gap-1 opacity-0 transition-all group-hover:opacity-100">
            <button
              type="button"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={() => setEditing(true)}
              className="rounded-md p-1 text-[var(--gray-text)] hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
              aria-label={`Edit ${card.title}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </button>
            <button
              type="button"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={() => onDelete(card.id)}
              className="rounded-md p-1 text-[var(--gray-text)] hover:bg-red-50 hover:text-red-400"
              aria-label={`Delete ${card.title}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h18" />
                <path d="M19 6l-1 14H6L5 6" />
                <path d="M8 6V4h8v2" />
              </svg>
            </button>
          </div>
        </div>
      </article>

      {editing && (
        <CardEditModal
          card={card}
          onClose={() => setEditing(false)}
          onSave={(fields) => {
            setEditing(false);
            onEdit(card.id, fields);
          }}
        />
      )}
    </>
  );
};
