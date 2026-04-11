import type { BoardData, Card, Column } from "@/lib/kanban";

// --- API response types ---

export type ApiCard = {
  id: number;
  column_id: number;
  title: string;
  details: string;
  priority: string;
  due_date: string | null;
  labels: string[];
  position: number;
};

export type ActivityEntry = {
  id: number;
  action: string;
  detail: string;
};

export type ApiColumn = {
  id: number;
  title: string;
  position: number;
  cards: ApiCard[];
};

export type ApiBoard = {
  id: number;
  title: string;
  columns: ApiColumn[];
};

export type ApiBoardSummary = {
  id: number;
  title: string;
};

// --- ID helpers ---

export const toColId = (id: number): string => `col-${id}`;
export const toCardId = (id: number): string => `card-${id}`;
export const fromColId = (id: string): number => parseInt(id.slice(4), 10);
export const fromCardId = (id: string): number => parseInt(id.slice(5), 10);

// --- Conversion ---

export const toBoardData = (board: ApiBoard): BoardData => {
  const cards: Record<string, Card> = {};
  const columns: Column[] = board.columns.map((col) => ({
    id: toColId(col.id),
    title: col.title,
    cardIds: col.cards.map((c) => {
      const cardId = toCardId(c.id);
      cards[cardId] = {
        id: cardId,
        title: c.title,
        details: c.details,
        priority: (c.priority as Card["priority"]) ?? "medium",
        due_date: c.due_date ?? null,
        labels: c.labels ?? [],
      };
      return cardId;
    }),
  }));
  return { columns, cards };
};

// --- Fetch helpers ---

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const headers: HeadersInit = init?.body ? { "Content-Type": "application/json" } : {};
  const res = await fetch(path, { ...init, headers });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res;
}

// --- Board management ---

export const listBoards = (): Promise<ApiBoardSummary[]> =>
  apiFetch("/api/boards").then((r) => r.json());

export const getBoardById = (id: number): Promise<ApiBoard> =>
  apiFetch(`/api/boards/${id}`).then((r) => r.json());

export const createBoard = (title: string): Promise<ApiBoard> =>
  apiFetch("/api/boards", {
    method: "POST",
    body: JSON.stringify({ title }),
  }).then((r) => r.json());

export const renameBoard = (id: number, title: string): Promise<ApiBoardSummary> =>
  apiFetch(`/api/boards/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  }).then((r) => r.json());

export const deleteBoard = (id: number): Promise<void> =>
  apiFetch(`/api/boards/${id}`, { method: "DELETE" }).then(() => undefined);

// --- Legacy: first board (used as fallback) ---

export const getBoard = (): Promise<ApiBoard> =>
  apiFetch("/api/board").then((r) => r.json());

// --- Cards ---

export const createCard = (
  column_id: number,
  title: string,
  details: string,
  priority = "medium",
  due_date: string | null = null,
  labels: string[] = []
): Promise<ApiCard> =>
  apiFetch("/api/cards", {
    method: "POST",
    body: JSON.stringify({ column_id, title, details, priority, due_date, labels }),
  }).then((r) => r.json());

export const updateCard = (
  id: number,
  fields: { title?: string; details?: string; priority?: string; due_date?: string | null; labels?: string[] }
): Promise<ApiCard> =>
  apiFetch(`/api/cards/${id}`, {
    method: "PATCH",
    body: JSON.stringify(fields),
  }).then((r) => r.json());

export const createColumn = (boardId: number, title: string): Promise<ApiColumn> =>
  apiFetch(`/api/boards/${boardId}/columns`, {
    method: "POST",
    body: JSON.stringify({ title }),
  }).then((r) => r.json());

export const deleteColumn = (columnId: number): Promise<void> =>
  apiFetch(`/api/columns/${columnId}`, { method: "DELETE" }).then(() => undefined);

export const getBoardActivity = (boardId: number): Promise<ActivityEntry[]> =>
  apiFetch(`/api/boards/${boardId}/activity`).then((r) => r.json());

export const deleteCard = (id: number): Promise<void> =>
  apiFetch(`/api/cards/${id}`, { method: "DELETE" }).then(() => undefined);

export const moveCard = (
  id: number,
  column_id: number,
  position: number
): Promise<ApiCard> =>
  apiFetch(`/api/cards/${id}/move`, {
    method: "PATCH",
    body: JSON.stringify({ column_id, position }),
  }).then((r) => r.json());

export const renameColumn = (id: number, title: string): Promise<ApiColumn> =>
  apiFetch(`/api/columns/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  }).then((r) => r.json());

// --- AI chat ---

type ChatBoard = {
  columns: Array<{
    id: number;
    title: string;
    cards: Array<{ id: number; title: string; details: string }>;
  }>;
};

export type AiChatResponse = {
  message: string;
  board_updated: boolean;
  operations: unknown[] | null;
};

export const toBoardForChat = (board: BoardData): ChatBoard => ({
  columns: board.columns.map((col) => ({
    id: fromColId(col.id),
    title: col.title,
    cards: col.cardIds.map((cardId) => {
      const card = board.cards[cardId];
      return { id: fromCardId(cardId), title: card.title, details: card.details };
    }),
  })),
});

export const aiChat = (
  messages: Array<{ role: string; content: string }>,
  board: ChatBoard
): Promise<AiChatResponse> =>
  apiFetch("/api/ai/chat", {
    method: "POST",
    body: JSON.stringify({ messages, board }),
  }).then((r) => r.json());
