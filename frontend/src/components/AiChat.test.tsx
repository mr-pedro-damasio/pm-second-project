import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { AiChat } from "@/components/AiChat";

// jsdom doesn't implement scrollIntoView
window.HTMLElement.prototype.scrollIntoView = vi.fn();

vi.mock("@/lib/api", () => ({
  aiChat: vi.fn(),
  toBoardForChat: vi.fn().mockReturnValue({ columns: [] }),
}));

import * as api from "@/lib/api";

const mockBoard = {
  columns: [{ id: "col-1", title: "Backlog", cardIds: [] }],
  cards: {},
};

describe("AiChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the chat panel with placeholder text", () => {
    render(<AiChat board={mockBoard} onBoardUpdate={vi.fn()} />);
    expect(screen.getByText(/ask me to create, move, or edit cards/i)).toBeInTheDocument();
  });

  it("send button is disabled when input is empty", () => {
    render(<AiChat board={mockBoard} onBoardUpdate={vi.fn()} />);
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("sends a message and shows user + assistant bubbles", async () => {
    vi.mocked(api.aiChat).mockResolvedValueOnce({
      message: "Sure, done!",
      board_updated: false,
      operations: null,
    });

    render(<AiChat board={mockBoard} onBoardUpdate={vi.fn()} />);

    await userEvent.type(screen.getByPlaceholderText(/ask the ai/i), "Hello AI");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(screen.getByText("Hello AI")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Sure, done!")).toBeInTheDocument());
  });

  it("send button is disabled while request is in flight", async () => {
    let resolve: (v: unknown) => void;
    vi.mocked(api.aiChat).mockReturnValueOnce(new Promise((r) => { resolve = r; }) as never);

    render(<AiChat board={mockBoard} onBoardUpdate={vi.fn()} />);

    await userEvent.type(screen.getByPlaceholderText(/ask the ai/i), "Hello");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(screen.getByRole("button", { name: /\.\.\./i })).toBeDisabled();

    resolve!({
      message: "Done",
      board_updated: false,
      operations: null,
    });
    await waitFor(() => expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument());
  });

  it("calls onBoardUpdate when board_updated is true", async () => {
    vi.mocked(api.aiChat).mockResolvedValueOnce({
      message: "Added a card!",
      board_updated: true,
      operations: null,
    });

    const onBoardUpdate = vi.fn().mockResolvedValue(undefined);
    render(<AiChat board={mockBoard} onBoardUpdate={onBoardUpdate} />);

    await userEvent.type(screen.getByPlaceholderText(/ask the ai/i), "Add a card");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => expect(onBoardUpdate).toHaveBeenCalledTimes(1));
  });

  it("does not call onBoardUpdate when board_updated is false", async () => {
    vi.mocked(api.aiChat).mockResolvedValueOnce({
      message: "Nothing changed.",
      board_updated: false,
      operations: null,
    });

    const onBoardUpdate = vi.fn().mockResolvedValue(undefined);
    render(<AiChat board={mockBoard} onBoardUpdate={onBoardUpdate} />);

    await userEvent.type(screen.getByPlaceholderText(/ask the ai/i), "How are things?");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => expect(screen.getByText("Nothing changed.")).toBeInTheDocument());
    expect(onBoardUpdate).not.toHaveBeenCalled();
  });

  it("shows error message on network failure", async () => {
    vi.mocked(api.aiChat).mockRejectedValueOnce(new Error("network"));

    render(<AiChat board={mockBoard} onBoardUpdate={vi.fn()} />);

    await userEvent.type(screen.getByPlaceholderText(/ask the ai/i), "Hello");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() =>
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
    );
  });

  it("clears input after sending", async () => {
    vi.mocked(api.aiChat).mockResolvedValueOnce({
      message: "Got it.",
      board_updated: false,
      operations: null,
    });

    render(<AiChat board={mockBoard} onBoardUpdate={vi.fn()} />);
    const input = screen.getByPlaceholderText(/ask the ai/i);

    await userEvent.type(input, "Hello");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(input).toHaveValue("");
  });
});
