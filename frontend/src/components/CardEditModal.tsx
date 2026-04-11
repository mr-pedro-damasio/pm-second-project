"use client";

import { useEffect, useRef, useState } from "react";
import type { Card, Priority } from "@/lib/kanban";

type Props = {
  card: Card;
  onSave: (fields: { title: string; details: string; priority: Priority; due_date: string | null; labels: string[] }) => void;
  onClose: () => void;
};

const PRIORITIES: { value: Priority; label: string; color: string }[] = [
  { value: "low", label: "Low", color: "bg-emerald-100 text-emerald-700" },
  { value: "medium", label: "Medium", color: "bg-amber-100 text-amber-700" },
  { value: "high", label: "High", color: "bg-red-100 text-red-600" },
];

export const CardEditModal = ({ card, onSave, onClose }: Props) => {
  const [title, setTitle] = useState(card.title);
  const [details, setDetails] = useState(card.details);
  const [priority, setPriority] = useState<Priority>(card.priority);
  const [dueDate, setDueDate] = useState(card.due_date ?? "");
  const [labels, setLabels] = useState<string[]>(card.labels ?? []);
  const [labelInput, setLabelInput] = useState("");
  const overlayRef = useRef<HTMLDivElement>(null);

  // Trap focus and close on Escape
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const handleSave = () => {
    const trimmed = title.trim();
    if (!trimmed) return;
    onSave({
      title: trimmed,
      details: details.trim(),
      priority,
      due_date: dueDate || null,
      labels,
    });
  };

  const addLabel = () => {
    const val = labelInput.trim();
    if (!val || labels.includes(val) || labels.length >= 10) return;
    setLabels([...labels, val]);
    setLabelInput("");
  };

  const removeLabel = (label: string) => {
    setLabels(labels.filter((l) => l !== label));
  };

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4 backdrop-blur-sm"
      onMouseDown={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div className="w-full max-w-md rounded-[28px] border border-[var(--stroke)] bg-white p-8 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <h2 className="font-display text-xl font-semibold text-[var(--navy-dark)]">
            Edit card
          </h2>
          <button
            onClick={onClose}
            className="rounded-xl p-1.5 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
            aria-label="Close"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="mt-6 flex flex-col gap-4">
          {/* Title */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Title
            </label>
            <input
              autoFocus
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20"
            />
          </div>

          {/* Details */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Details
            </label>
            <textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              rows={3}
              className="rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none resize-none focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20"
            />
          </div>

          {/* Priority */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Priority
            </label>
            <div className="flex gap-2">
              {PRIORITIES.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setPriority(p.value)}
                  className={`flex-1 rounded-xl border px-3 py-2 text-xs font-semibold transition-all ${
                    priority === p.value
                      ? `${p.color} border-transparent ring-2 ring-offset-1 ring-[var(--primary-blue)]`
                      : "border-[var(--stroke)] text-[var(--gray-text)] hover:border-[var(--navy-dark)]"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Due date */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Due date
            </label>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20"
            />
            {dueDate && (
              <button
                type="button"
                onClick={() => setDueDate("")}
                className="self-start text-xs text-[var(--gray-text)] hover:text-red-500"
              >
                Clear date
              </button>
            )}
          </div>

          {/* Labels */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Labels
            </label>
            {labels.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {labels.map((label) => (
                  <span
                    key={label}
                    className="flex items-center gap-1 rounded-full bg-[var(--surface)] px-2.5 py-1 text-xs font-medium text-[var(--navy-dark)]"
                  >
                    {label}
                    <button
                      type="button"
                      onClick={() => removeLabel(label)}
                      aria-label={`Remove label ${label}`}
                      className="text-[var(--gray-text)] hover:text-red-500"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </span>
                ))}
              </div>
            )}
            {labels.length < 10 && (
              <div className="flex gap-2">
                <input
                  value={labelInput}
                  onChange={(e) => setLabelInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") { e.preventDefault(); addLabel(); }
                  }}
                  placeholder="Add a label..."
                  className="min-w-0 flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-xs text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                />
                <button
                  type="button"
                  onClick={addLabel}
                  disabled={!labelInput.trim()}
                  className="rounded-xl border border-[var(--stroke)] px-3 py-2 text-xs font-semibold text-[var(--primary-blue)] hover:bg-[var(--surface)] disabled:opacity-40"
                >
                  Add
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-xl border border-[var(--stroke)] px-5 py-2.5 text-sm font-semibold text-[var(--gray-text)] hover:border-[var(--navy-dark)] hover:text-[var(--navy-dark)]"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!title.trim()}
            className="rounded-xl bg-[var(--purple-secondary)] px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};
