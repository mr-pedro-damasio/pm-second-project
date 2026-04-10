import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  createCard,
  deleteCard,
  fromCardId,
  fromColId,
  getBoard,
  moveCard,
  renameColumn,
  toBoardData,
  toCardId,
  toColId,
} from "./api";

const mockOk = (data: unknown, status = 200) =>
  Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
  } as Response);

describe("api", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // --- ID helpers ---

  it("toColId / fromColId round-trip", () => {
    expect(toColId(3)).toBe("col-3");
    expect(fromColId("col-3")).toBe(3);
  });

  it("toCardId / fromCardId round-trip", () => {
    expect(toCardId(7)).toBe("card-7");
    expect(fromCardId("card-7")).toBe(7);
  });

  // --- toBoardData ---

  it("toBoardData converts API board to BoardData", () => {
    const data = {
      id: 1,
      title: "My Board",
      columns: [
        {
          id: 1,
          title: "Backlog",
          position: 0,
          cards: [
            { id: 1, column_id: 1, title: "A card", details: "Details", position: 0 },
          ],
        },
      ],
    };
    const board = toBoardData(data);
    expect(board.columns).toHaveLength(1);
    expect(board.columns[0].id).toBe("col-1");
    expect(board.columns[0].title).toBe("Backlog");
    expect(board.columns[0].cardIds).toEqual(["card-1"]);
    expect(board.cards["card-1"]).toEqual({ id: "card-1", title: "A card", details: "Details" });
  });

  // --- fetch helpers ---

  it("getBoard fetches GET /api/board", async () => {
    vi.mocked(fetch).mockReturnValueOnce(
      mockOk({ id: 1, title: "My Board", columns: [] })
    );
    const result = await getBoard();
    expect(fetch).toHaveBeenCalledWith(
      "/api/board",
      expect.objectContaining({ headers: expect.any(Object) })
    );
    expect(result.id).toBe(1);
  });

  it("createCard posts to /api/cards", async () => {
    vi.mocked(fetch).mockReturnValueOnce(
      mockOk({ id: 5, column_id: 1, title: "Test", details: "", position: 0 })
    );
    const result = await createCard(1, "Test", "");
    expect(fetch).toHaveBeenCalledWith(
      "/api/cards",
      expect.objectContaining({ method: "POST" })
    );
    expect(result.id).toBe(5);
  });

  it("deleteCard sends DELETE /api/cards/{id}", async () => {
    vi.mocked(fetch).mockReturnValueOnce(mockOk(null, 204));
    await deleteCard(5);
    expect(fetch).toHaveBeenCalledWith(
      "/api/cards/5",
      expect.objectContaining({ method: "DELETE" })
    );
  });

  it("moveCard sends PATCH /api/cards/{id}/move", async () => {
    vi.mocked(fetch).mockReturnValueOnce(
      mockOk({ id: 5, column_id: 2, title: "Test", details: "", position: 1 })
    );
    await moveCard(5, 2, 1);
    expect(fetch).toHaveBeenCalledWith(
      "/api/cards/5/move",
      expect.objectContaining({ method: "PATCH" })
    );
  });

  it("renameColumn sends PATCH /api/columns/{id}", async () => {
    vi.mocked(fetch).mockReturnValueOnce(
      mockOk({ id: 1, title: "New", position: 0, cards: [] })
    );
    await renameColumn(1, "New");
    expect(fetch).toHaveBeenCalledWith(
      "/api/columns/1",
      expect.objectContaining({ method: "PATCH" })
    );
  });

  it("throws on non-ok response", async () => {
    vi.mocked(fetch).mockReturnValueOnce(mockOk({ detail: "Unauthorized" }, 401));
    await expect(getBoard()).rejects.toThrow("API error: 401");
  });
});
