"use client";

import { useEffect, useRef, useState } from "react";
import type { ApiBoardSummary } from "@/lib/api";
import * as api from "@/lib/api";

type Props = {
  boards: ApiBoardSummary[];
  activeBoardId: number;
  onSelect: (boardId: number) => void;
  onBoardsChange: () => void;
};

export const BoardSelector = ({
  boards,
  activeBoardId,
  onSelect,
  onBoardsChange,
}: Props) => {
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [renameTitle, setRenameTitle] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
        setCreating(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const activeBoard = boards.find((b) => b.id === activeBoardId);

  const handleCreate = async () => {
    const title = newTitle.trim();
    if (!title || busy) return;
    setBusy(true);
    try {
      const board = await api.createBoard(title);
      setNewTitle("");
      setCreating(false);
      onBoardsChange();
      onSelect(board.id);
      setOpen(false);
    } catch {
      // ignore
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, boardId: number) => {
    e.stopPropagation();
    if (busy) return;
    setBusy(true);
    try {
      await api.deleteBoard(boardId);
      onBoardsChange();
      if (boardId === activeBoardId) {
        const remaining = boards.find((b) => b.id !== boardId);
        if (remaining) onSelect(remaining.id);
      }
    } catch {
      // ignore
    } finally {
      setBusy(false);
    }
  };

  const handleRenameStart = (e: React.MouseEvent, board: ApiBoardSummary) => {
    e.stopPropagation();
    setRenamingId(board.id);
    setRenameTitle(board.title);
  };

  const handleRenameCommit = async (boardId: number) => {
    const title = renameTitle.trim();
    if (!title || busy) {
      setRenamingId(null);
      return;
    }
    setBusy(true);
    try {
      await api.renameBoard(boardId, title);
      onBoardsChange();
    } catch {
      // ignore
    } finally {
      setRenamingId(null);
      setBusy(false);
    }
  };

  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2.5 text-sm font-semibold text-[var(--navy-dark)] transition-colors hover:border-[var(--primary-blue)]"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-[var(--primary-blue)]"
        >
          <rect x="3" y="3" width="7" height="7" />
          <rect x="14" y="3" width="7" height="7" />
          <rect x="3" y="14" width="7" height="7" />
          <rect x="14" y="14" width="7" height="7" />
        </svg>
        <span className="max-w-[140px] truncate">{activeBoard?.title ?? "Board"}</span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div className="absolute left-0 top-full z-50 mt-2 w-64 rounded-2xl border border-[var(--stroke)] bg-white py-2 shadow-lg">
          <p className="px-4 pb-2 pt-1 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Your boards
          </p>

          {boards.map((board) => (
            <div
              key={board.id}
              onClick={() => {
                if (renamingId === board.id) return;
                onSelect(board.id);
                setOpen(false);
              }}
              className={`group flex cursor-pointer items-center gap-2 px-4 py-2 text-sm transition-colors hover:bg-[var(--surface)] ${
                board.id === activeBoardId
                  ? "font-semibold text-[var(--navy-dark)]"
                  : "text-[var(--gray-text)]"
              }`}
            >
              {board.id === activeBoardId && (
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--accent-yellow)]" />
              )}
              {renamingId === board.id ? (
                <input
                  autoFocus
                  value={renameTitle}
                  onChange={(e) => setRenameTitle(e.target.value)}
                  onBlur={() => handleRenameCommit(board.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleRenameCommit(board.id);
                    if (e.key === "Escape") setRenamingId(null);
                  }}
                  onClick={(e) => e.stopPropagation()}
                  className="min-w-0 flex-1 rounded border border-[var(--primary-blue)] bg-white px-2 py-0.5 text-sm text-[var(--navy-dark)] outline-none"
                />
              ) : (
                <span className="min-w-0 flex-1 truncate">{board.title}</span>
              )}
              <div className="flex shrink-0 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                <button
                  onClick={(e) => handleRenameStart(e, board)}
                  title="Rename board"
                  className="rounded p-0.5 text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                </button>
                {boards.length > 1 && (
                  <button
                    onClick={(e) => handleDelete(e, board.id)}
                    title="Delete board"
                    className="rounded p-0.5 text-[var(--gray-text)] hover:text-red-500"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6l-1 14H6L5 6" />
                      <path d="M10 11v6M14 11v6" />
                      <path d="M9 6V4h6v2" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          ))}

          <div className="mx-4 my-2 border-t border-[var(--stroke)]" />

          {creating ? (
            <div className="px-4 py-2">
              <input
                autoFocus
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCreate();
                  if (e.key === "Escape") {
                    setCreating(false);
                    setNewTitle("");
                  }
                }}
                placeholder="Board name..."
                className="w-full rounded-lg border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
              />
              <div className="mt-2 flex gap-2">
                <button
                  onClick={handleCreate}
                  disabled={busy || !newTitle.trim()}
                  className="flex-1 rounded-lg bg-[var(--purple-secondary)] px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                >
                  Create
                </button>
                <button
                  onClick={() => { setCreating(false); setNewTitle(""); }}
                  className="rounded-lg border border-[var(--stroke)] px-3 py-1.5 text-xs text-[var(--gray-text)]"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setCreating(true)}
              className="flex w-full items-center gap-2 px-4 py-2 text-sm text-[var(--primary-blue)] hover:bg-[var(--surface)]"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              New board
            </button>
          )}
        </div>
      )}
    </div>
  );
};
