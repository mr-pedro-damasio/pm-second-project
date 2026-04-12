"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  pointerWithin,
  rectIntersection,
  useSensor,
  useSensors,
  type CollisionDetection,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { AiChat } from "@/components/AiChat";
import { BoardSelector } from "@/components/BoardSelector";
import { ActivityPanel } from "@/components/ActivityPanel";
import { moveCard as moveCardLocally, type BoardData, type Priority } from "@/lib/kanban";
import * as api from "@/lib/api";
import type { ApiBoardSummary } from "@/lib/api";

// Prefer pointer position over geometry — prevents "adjacent column" misdrops.
const collisionDetection: CollisionDetection = (args) => {
  const within = pointerWithin(args);
  return within.length > 0 ? within : rectIntersection(args);
};

export const KanbanBoard = () => {
  const [boards, setBoards] = useState<ApiBoardSummary[]>([]);
  const [activeBoardId, setActiveBoardId] = useState<number | null>(null);
  const [board, setBoard] = useState<BoardData>({ columns: [], cards: {} });
  const [boardTitle, setBoardTitle] = useState("My Board");
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [showActivity, setShowActivity] = useState(false);
  const [newColumnTitle, setNewColumnTitle] = useState("");
  const [addingColumn, setAddingColumn] = useState(false);

  const loadBoards = useCallback(async () => {
    const list = await api.listBoards();
    setBoards(list);
    return list;
  }, []);

  const loadBoard = useCallback(async (boardId: number) => {
    const data = await api.getBoardById(boardId);
    setBoard(api.toBoardData(data));
    setBoardTitle(data.title);
  }, []);

  useEffect(() => {
    const init = async () => {
      try {
        const list = await loadBoards();
        if (list.length > 0) {
          setActiveBoardId(list[0].id);
          await loadBoard(list[0].id);
        }
      } catch {
        setFetchError("Could not load the board. Please refresh.");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [loadBoards, loadBoard]);

  const handleSelectBoard = useCallback(async (boardId: number) => {
    setActiveBoardId(boardId);
    setLoading(true);
    setFetchError(null);
    try {
      await loadBoard(boardId);
    } catch {
      setFetchError("Could not load board.");
    } finally {
      setLoading(false);
    }
  }, [loadBoard]);

  const handleBoardsChange = useCallback(async () => {
    const list = await loadBoards();
    // If current board was deleted, switch to first remaining
    if (activeBoardId && !list.find((b) => b.id === activeBoardId)) {
      if (list.length > 0) {
        await handleSelectBoard(list[0].id);
      }
    } else if (activeBoardId) {
      // Reload current board in case it was renamed
      const updated = list.find((b) => b.id === activeBoardId);
      if (updated) setBoardTitle(updated.title);
    }
  }, [loadBoards, activeBoardId, handleSelectBoard]);

  const fetchCurrentBoard = useCallback(async () => {
    if (activeBoardId) await loadBoard(activeBoardId);
  }, [activeBoardId, loadBoard]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  const cardsById = useMemo(() => board.cards, [board.cards]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);
    if (!over || active.id === over.id || busy) return;

    const prevBoard = board;
    const nextColumns = moveCardLocally(
      board.columns,
      active.id as string,
      over.id as string
    );
    const targetCol = nextColumns.find((col) =>
      col.cardIds.includes(active.id as string)
    );
    if (!targetCol) return;
    const newPosition = targetCol.cardIds.indexOf(active.id as string);

    setBoard((prev) => ({ ...prev, columns: nextColumns }));
    setBusy(true);
    try {
      await api.moveCard(
        api.fromCardId(active.id as string),
        api.fromColId(targetCol.id),
        newPosition
      );
    } catch {
      setBoard(prevBoard);
    } finally {
      setBusy(false);
    }
  };

  const handleRenameColumn = async (columnId: string, title: string) => {
    const prevTitle =
      board.columns.find((col) => col.id === columnId)?.title ?? title;
    setBoard((prev) => ({
      ...prev,
      columns: prev.columns.map((col) =>
        col.id === columnId ? { ...col, title } : col
      ),
    }));
    try {
      await api.renameColumn(api.fromColId(columnId), title);
    } catch {
      setBoard((prev) => ({
        ...prev,
        columns: prev.columns.map((col) =>
          col.id === columnId ? { ...col, title: prevTitle } : col
        ),
      }));
    }
  };

  const handleAddCard = async (
    columnId: string,
    title: string,
    details: string
  ) => {
    if (busy) return;
    setBusy(true);
    try {
      const card = await api.createCard(api.fromColId(columnId), title, details);
      const id = api.toCardId(card.id);
      setBoard((prev) => ({
        ...prev,
        cards: {
          ...prev.cards,
          [id]: {
            id,
            title: card.title,
            details: card.details,
            priority: (card.priority as Priority) ?? "medium",
            due_date: card.due_date ?? null,
            labels: card.labels ?? [],
          },
        },
        columns: prev.columns.map((col) =>
          col.id === columnId
            ? { ...col, cardIds: [...col.cardIds, id] }
            : col
        ),
      }));
    } catch {
      // silently fail — user can retry
    } finally {
      setBusy(false);
    }
  };

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  };

  const handleEditCard = async (
    cardId: string,
    fields: { title: string; details: string; priority: Priority; due_date: string | null; labels: string[] }
  ) => {
    if (busy) return;
    setBusy(true);
    try {
      const updated = await api.updateCard(api.fromCardId(cardId), fields);
      setBoard((prev) => ({
        ...prev,
        cards: {
          ...prev.cards,
          [cardId]: {
            id: cardId,
            title: updated.title,
            details: updated.details,
            priority: (updated.priority as Priority) ?? "medium",
            due_date: updated.due_date ?? null,
            labels: updated.labels ?? [],
          },
        },
      }));
    } catch {
      // silently fail
    } finally {
      setBusy(false);
    }
  };

  const handleAddColumn = async (title: string) => {
    if (!activeBoardId || busy) return;
    setBusy(true);
    try {
      const col = await api.createColumn(activeBoardId, title);
      setBoard((prev) => ({
        ...prev,
        columns: [
          ...prev.columns,
          { id: api.toColId(col.id), title: col.title, cardIds: [] },
        ],
      }));
    } catch {
      // silently fail
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteColumn = async (columnId: string) => {
    if (busy) return;
    const prevBoard = board;
    setBoard((prev) => ({
      ...prev,
      columns: prev.columns.filter((col) => col.id !== columnId),
    }));
    setBusy(true);
    try {
      await api.deleteColumn(api.fromColId(columnId));
    } catch {
      setBoard(prevBoard);
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    if (busy) return;
    setBusy(true);
    try {
      await api.deleteCard(api.fromCardId(cardId));
      setBoard((prev) => ({
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((col) =>
          col.id === columnId
            ? { ...col, cardIds: col.cardIds.filter((id) => id !== cardId) }
            : col
        ),
      }));
    } catch {
      // silently fail
    } finally {
      setBusy(false);
    }
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative">
      {/* Background blobs */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
        <div className="absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />
      </div>

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Project Management
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                pm-project
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Manage multiple boards, drag cards between stages, and get AI
                assistance to keep your projects moving.
              </p>
            </div>
            <div className="flex flex-wrap items-start gap-3">
              {boards.length > 0 && activeBoardId !== null && (
                <BoardSelector
                  boards={boards}
                  activeBoardId={activeBoardId}
                  onSelect={handleSelectBoard}
                  onBoardsChange={handleBoardsChange}
                />
              )}
              <button
                onClick={handleLogout}
                className="rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)] transition-colors hover:border-[var(--navy-dark)] hover:text-[var(--navy-dark)]"
              >
                Sign out
              </button>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]">
              <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
              {boardTitle}
            </div>
            <span className="text-xs text-[var(--gray-text)]">
              {board.columns.length} columns &middot;{" "}
              {Object.keys(board.cards).length} cards
            </span>
          </div>
        </header>

        {loading ? (
          <p className="text-sm text-[var(--gray-text)]">Loading board...</p>
        ) : fetchError ? (
          <p className="text-sm text-red-500">{fetchError}</p>
        ) : (
          <div className="flex items-start gap-6">
            <div className="relative min-w-0 flex-1">
              <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-[var(--surface)] to-transparent" />
              <div className="columns-scroll overflow-x-auto pb-3">
                <DndContext
                  sensors={sensors}
                  collisionDetection={collisionDetection}
                  onDragStart={handleDragStart}
                  onDragEnd={handleDragEnd}
                >
                  <section
                    className={`flex gap-4 ${busy ? "pointer-events-none opacity-70" : ""}`}
                  >
                    {board.columns.map((column) => (
                      <KanbanColumn
                        key={column.id}
                        column={column}
                        cards={column.cardIds.map((cardId) => board.cards[cardId])}
                        onRename={handleRenameColumn}
                        onAddCard={handleAddCard}
                        onDeleteCard={handleDeleteCard}
                        onEditCard={handleEditCard}
                        onDeleteColumn={handleDeleteColumn}
                        canDelete={board.columns.length > 1}
                      />
                    ))}
                    {/* Add new column */}
                    {addingColumn ? (
                      <div className="flex w-[220px] shrink-0 flex-col gap-2 rounded-3xl border border-dashed border-[var(--stroke)] p-4">
                        <input
                          autoFocus
                          value={newColumnTitle}
                          onChange={(e) => setNewColumnTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && newColumnTitle.trim()) {
                              handleAddColumn(newColumnTitle.trim());
                              setNewColumnTitle("");
                              setAddingColumn(false);
                            }
                            if (e.key === "Escape") {
                              setAddingColumn(false);
                              setNewColumnTitle("");
                            }
                          }}
                          placeholder="Column name..."
                          className="rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              if (newColumnTitle.trim()) {
                                handleAddColumn(newColumnTitle.trim());
                                setNewColumnTitle("");
                                setAddingColumn(false);
                              }
                            }}
                            disabled={!newColumnTitle.trim()}
                            className="flex-1 rounded-xl bg-[var(--purple-secondary)] px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                          >
                            Add
                          </button>
                          <button
                            onClick={() => { setAddingColumn(false); setNewColumnTitle(""); }}
                            className="rounded-xl border border-[var(--stroke)] px-3 py-1.5 text-xs text-[var(--gray-text)]"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => setAddingColumn(true)}
                        className="flex h-12 w-[220px] shrink-0 items-center justify-center gap-2 rounded-3xl border border-dashed border-[var(--stroke)] text-sm font-semibold text-[var(--gray-text)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                        New column
                      </button>
                    )}
                  </section>
                  <DragOverlay>
                    {activeCard ? (
                      <div className="w-[260px]">
                        <KanbanCardPreview card={activeCard} />
                      </div>
                    ) : null}
                  </DragOverlay>
                </DndContext>
              </div>
            </div>
            <div className="flex shrink-0 flex-col gap-4">
              <AiChat board={board} onBoardUpdate={fetchCurrentBoard} />
              {activeBoardId && (
                <div>
                  <button
                    onClick={() => setShowActivity((v) => !v)}
                    className="mb-2 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)] transition-colors hover:border-[var(--navy-dark)] hover:text-[var(--navy-dark)]"
                  >
                    {showActivity ? "Hide" : "Show"} activity
                  </button>
                  {showActivity && <ActivityPanel boardId={activeBoardId} />}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
