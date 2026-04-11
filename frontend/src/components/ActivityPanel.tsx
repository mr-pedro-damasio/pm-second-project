"use client";

import { useEffect, useState } from "react";
import * as api from "@/lib/api";
import type { ActivityEntry } from "@/lib/api";

const ACTION_LABELS: Record<string, string> = {
  card_created: "Card added",
  card_deleted: "Card deleted",
  card_moved: "Card moved",
  column_added: "Column added",
  column_deleted: "Column deleted",
};

type Props = {
  boardId: number;
};

export const ActivityPanel = ({ boardId }: Props) => {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getBoardActivity(boardId)
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [boardId]);

  return (
    <div className="w-[260px] rounded-2xl border border-[var(--stroke)] bg-white p-4 shadow-[var(--shadow)]">
      <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
        Recent activity
      </p>
      {loading ? (
        <p className="text-xs text-[var(--gray-text)]">Loading...</p>
      ) : entries.length === 0 ? (
        <p className="text-xs text-[var(--gray-text)]">No activity yet.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {entries.map((entry) => (
            <li key={entry.id} className="flex flex-col gap-0.5">
              <span className="text-xs font-semibold text-[var(--navy-dark)]">
                {ACTION_LABELS[entry.action] ?? entry.action}
              </span>
              {entry.detail && (
                <span className="truncate text-[11px] text-[var(--gray-text)]">
                  {entry.detail}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
