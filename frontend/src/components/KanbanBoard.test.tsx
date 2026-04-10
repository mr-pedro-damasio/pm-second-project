import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";

vi.mock("@/lib/api", () => {
  const mockBoard = {
    columns: [
      { id: "col-1", title: "Backlog", cardIds: ["card-1", "card-2"] },
      { id: "col-2", title: "Discovery", cardIds: ["card-3"] },
      { id: "col-3", title: "In Progress", cardIds: ["card-4", "card-5"] },
      { id: "col-4", title: "Review", cardIds: ["card-6"] },
      { id: "col-5", title: "Done", cardIds: ["card-7", "card-8"] },
    ],
    cards: {
      "card-1": { id: "card-1", title: "Card 1", details: "" },
      "card-2": { id: "card-2", title: "Card 2", details: "" },
      "card-3": { id: "card-3", title: "Card 3", details: "" },
      "card-4": { id: "card-4", title: "Card 4", details: "" },
      "card-5": { id: "card-5", title: "Card 5", details: "" },
      "card-6": { id: "card-6", title: "Card 6", details: "" },
      "card-7": { id: "card-7", title: "Card 7", details: "" },
      "card-8": { id: "card-8", title: "Card 8", details: "" },
    },
  };
  return {
    getBoard: vi.fn().mockResolvedValue({}),
    toBoardData: vi.fn().mockReturnValue(mockBoard),
    createCard: vi
      .fn()
      .mockResolvedValue({ id: 99, column_id: 1, title: "New card", details: "Notes", position: 2 }),
    deleteCard: vi.fn().mockResolvedValue(undefined),
    moveCard: vi.fn().mockResolvedValue({ id: 1, column_id: 1, title: "", details: "", position: 0 }),
    renameColumn: vi.fn().mockResolvedValue({ id: 1, title: "New Name", position: 0, cards: [] }),
    fromColId: (id: string) => parseInt(id.slice(4), 10),
    fromCardId: (id: string) => parseInt(id.slice(5), 10),
    toCardId: (id: number) => `card-${id}`,
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
});
