import type { Card, Priority } from "@/lib/kanban";

const PRIORITY_STYLES: Record<Priority, string> = {
  low: "bg-emerald-100 text-emerald-700",
  medium: "bg-amber-100 text-amber-700",
  high: "bg-red-100 text-red-600",
};

type KanbanCardPreviewProps = {
  card: Card;
};

export const KanbanCardPreview = ({ card }: KanbanCardPreviewProps) => (
  <article className="rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_18px_32px_rgba(3,33,71,0.16)]">
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0 flex-1">
        <h4 className="font-display text-base font-semibold text-[var(--navy-dark)]">
          {card.title}
        </h4>
        {card.details && (
          <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
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
            <span className="rounded-full bg-[var(--surface)] px-2 py-0.5 text-[10px] font-semibold text-[var(--gray-text)]">
              {card.due_date}
            </span>
          )}
        </div>
      </div>
    </div>
  </article>
);
