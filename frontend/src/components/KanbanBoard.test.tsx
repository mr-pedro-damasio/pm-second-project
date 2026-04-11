import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";

vi.mock("@/lib/api", () => {
  const mkCard = (id: number, colId: number, title: string) => ({
    id, column_id: colId, title, details: "", priority: "medium", due_date: null, labels: [], position: 0,
  });
  const mockApiBoard = {
    id: 1,
    title: "My Board",
    columns: [
      { id: 1, title: "Backlog", position: 0, cards: [mkCard(1, 1, "Card 1"), mkCard(2, 1, "Card 2")] },
      { id: 2, title: "Discovery", position: 1, cards: [mkCard(3, 2, "Card 3")] },
      { id: 3, title: "In Progress", position: 2, cards: [mkCard(4, 3, "Card 4"), mkCard(5, 3, "Card 5")] },
      { id: 4, title: "Review", position: 3, cards: [mkCard(6, 4, "Card 6")] },
      { id: 5, title: "Done", position: 4, cards: [mkCard(7, 5, "Card 7"), mkCard(8, 5, "Card 8")] },
    ],
  };
  const mkBoardCard = (id: string, title: string) => ({
    id, title, details: "", priority: "medium" as const, due_date: null, labels: [],
  });
  const mockBoardData = {
    columns: [
      { id: "col-1", title: "Backlog", cardIds: ["card-1", "card-2"] },
      { id: "col-2", title: "Discovery", cardIds: ["card-3"] },
      { id: "col-3", title: "In Progress", cardIds: ["card-4", "card-5"] },
      { id: "col-4", title: "Review", cardIds: ["card-6"] },
      { id: "col-5", title: "Done", cardIds: ["card-7", "card-8"] },
    ],
    cards: {
      "card-1": mkBoardCard("card-1", "Card 1"),
      "card-2": mkBoardCard("card-2", "Card 2"),
      "card-3": mkBoardCard("card-3", "Card 3"),
      "card-4": mkBoardCard("card-4", "Card 4"),
      "card-5": mkBoardCard("card-5", "Card 5"),
      "card-6": mkBoardCard("card-6", "Card 6"),
      "card-7": mkBoardCard("card-7", "Card 7"),
      "card-8": mkBoardCard("card-8", "Card 8"),
    },
  };
  return {
    listBoards: vi.fn().mockResolvedValue([{ id: 1, title: "My Board" }]),
    getBoardById: vi.fn().mockResolvedValue(mockApiBoard),
    getBoard: vi.fn().mockResolvedValue(mockApiBoard),
    toBoardData: vi.fn().mockReturnValue(mockBoardData),
    createBoard: vi.fn().mockResolvedValue({ id: 2, title: "New Board", columns: [] }),
    renameBoard: vi.fn().mockResolvedValue({ id: 1, title: "Renamed" }),
    deleteBoard: vi.fn().mockResolvedValue(undefined),
    createCard: vi
      .fn()
      .mockResolvedValue({ id: 99, column_id: 1, title: "New card", details: "Notes", priority: "medium", due_date: null, labels: [], position: 2 }),
    updateCard: vi
      .fn()
      .mockResolvedValue({ id: 99, column_id: 1, title: "Updated", details: "", priority: "medium", due_date: null, labels: [], position: 0 }),
    deleteCard: vi.fn().mockResolvedValue(undefined),
    moveCard: vi.fn().mockResolvedValue({ id: 1, column_id: 1, title: "", details: "", position: 0 }),
    renameColumn: vi.fn().mockResolvedValue({ id: 1, title: "New Name", position: 0, cards: [] }),
    createColumn: vi.fn().mockResolvedValue({ id: 6, title: "New Column", position: 5, cards: [] }),
    deleteColumn: vi.fn().mockResolvedValue(undefined),
    getBoardActivity: vi.fn().mockResolvedValue([]),
    fromColId: (id: string) => parseInt(id.slice(4), 10),
    fromCardId: (id: string) => parseInt(id.slice(5), 10),
    toCardId: (id: number) => `card-${id}`,
    toColId: (id: number) => `col-${id}`,
  };
});

const getFirstColumn = async () => (await screen.findAllByTestId(/column-/i))[0];

describe("KanbanBoard", () => {
  it("renders five columns", async () => {
    render(<KanbanBoard />);
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    const column = await getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    const column = await getFirstColumn();

    await userEvent.click(
      within(column).getByRole("button", { name: /add a card/i })
    );
    await userEvent.type(within(column).getByPlaceholderText(/card title/i), "New card");
    await userEvent.type(within(column).getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(await within(column).findByText("New card")).toBeInTheDocument();

    await userEvent.click(
      within(column).getByRole("button", { name: /delete new card/i })
    );

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });

  it("shows new column button", async () => {
    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);
    expect(screen.getByRole("button", { name: /new column/i })).toBeInTheDocument();
  });

  it("opens new column input when new column button is clicked", async () => {
    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);
    await userEvent.click(screen.getByRole("button", { name: /new column/i }));
    expect(screen.getByPlaceholderText(/column name/i)).toBeInTheDocument();
  });

  it("shows delete column buttons for each column", async () => {
    render(<KanbanBoard />);
    const columns = await screen.findAllByTestId(/column-/i);
    // Delete buttons should exist (one per column)
    const deleteBtns = screen.getAllByTitle(/delete column/i);
    expect(deleteBtns.length).toBe(columns.length);
  });

  it("shows activity toggle button", async () => {
    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);
    expect(screen.getByRole("button", { name: /show activity/i })).toBeInTheDocument();
  });
});
