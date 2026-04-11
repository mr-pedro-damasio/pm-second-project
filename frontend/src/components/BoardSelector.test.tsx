import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { BoardSelector } from "@/components/BoardSelector";
import * as api from "@/lib/api";

vi.mock("@/lib/api", () => ({
  createBoard: vi.fn(),
  renameBoard: vi.fn(),
  deleteBoard: vi.fn(),
}));

const boards = [
  { id: 1, title: "My Board" },
  { id: 2, title: "Sprint Board" },
];

describe("BoardSelector", () => {
  const onSelect = vi.fn();
  const onBoardsChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows active board title on the trigger button", () => {
    render(
      <BoardSelector
        boards={boards}
        activeBoardId={1}
        onSelect={onSelect}
        onBoardsChange={onBoardsChange}
      />
    );
    expect(screen.getByRole("button", { name: /my board/i })).toBeInTheDocument();
  });

  it("opens dropdown listing all boards when clicked", async () => {
    render(
      <BoardSelector
        boards={boards}
        activeBoardId={1}
        onSelect={onSelect}
        onBoardsChange={onBoardsChange}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /my board/i }));
    expect(screen.getByText("Sprint Board")).toBeInTheDocument();
    expect(screen.getAllByText("My Board").length).toBeGreaterThan(0);
  });

  it("calls onSelect when a board is clicked", async () => {
    render(
      <BoardSelector
        boards={boards}
        activeBoardId={1}
        onSelect={onSelect}
        onBoardsChange={onBoardsChange}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /my board/i }));
    await userEvent.click(screen.getByText("Sprint Board"));
    expect(onSelect).toHaveBeenCalledWith(2);
  });

  it("creates a new board when name is entered and Create is clicked", async () => {
    vi.mocked(api.createBoard).mockResolvedValue({
      id: 3,
      title: "New Project",
      columns: [],
    });
    render(
      <BoardSelector
        boards={boards}
        activeBoardId={1}
        onSelect={onSelect}
        onBoardsChange={onBoardsChange}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /my board/i }));
    await userEvent.click(screen.getByText("New board"));
    await userEvent.type(screen.getByPlaceholderText("Board name..."), "New Project");
    await userEvent.click(screen.getByRole("button", { name: /^create$/i }));
    expect(api.createBoard).toHaveBeenCalledWith("New Project");
    expect(onBoardsChange).toHaveBeenCalled();
    expect(onSelect).toHaveBeenCalledWith(3);
  });

  it("cancels board creation when Cancel is clicked", async () => {
    render(
      <BoardSelector
        boards={boards}
        activeBoardId={1}
        onSelect={onSelect}
        onBoardsChange={onBoardsChange}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /my board/i }));
    await userEvent.click(screen.getByText("New board"));
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByPlaceholderText("Board name...")).not.toBeInTheDocument();
  });

  it("deletes a board when delete button is clicked", async () => {
    vi.mocked(api.deleteBoard).mockResolvedValue(undefined);
    render(
      <BoardSelector
        boards={boards}
        activeBoardId={1}
        onSelect={onSelect}
        onBoardsChange={onBoardsChange}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /my board/i }));
    // hover over Sprint Board row to reveal its delete button
    const sprintRow = screen.getByText("Sprint Board").closest("div")!;
    await userEvent.hover(sprintRow);
    await userEvent.click(within(sprintRow).getByTitle("Delete board"));
    expect(api.deleteBoard).toHaveBeenCalledWith(2);
    expect(onBoardsChange).toHaveBeenCalled();
  });
});
