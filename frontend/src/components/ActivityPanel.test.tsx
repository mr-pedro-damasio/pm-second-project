import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { ActivityPanel } from "@/components/ActivityPanel";

vi.mock("@/lib/api", () => ({
  getBoardActivity: vi.fn(),
}));

import * as api from "@/lib/api";

describe("ActivityPanel", () => {
  it("shows loading initially", () => {
    vi.mocked(api.getBoardActivity).mockReturnValue(new Promise(() => {}));
    render(<ActivityPanel boardId={1} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows 'No activity yet' when empty", async () => {
    vi.mocked(api.getBoardActivity).mockResolvedValue([]);
    render(<ActivityPanel boardId={1} />);
    expect(await screen.findByText(/no activity yet/i)).toBeInTheDocument();
  });

  it("renders activity entries", async () => {
    vi.mocked(api.getBoardActivity).mockResolvedValue([
      { id: 1, action: "card_created", detail: "My Card" },
      { id: 2, action: "card_moved", detail: "" },
    ]);
    render(<ActivityPanel boardId={1} />);
    expect(await screen.findByText("Card added")).toBeInTheDocument();
    expect(screen.getByText("My Card")).toBeInTheDocument();
    expect(screen.getByText("Card moved")).toBeInTheDocument();
  });

  it("fetches activity for given boardId", async () => {
    vi.mocked(api.getBoardActivity).mockResolvedValue([]);
    render(<ActivityPanel boardId={42} />);
    await screen.findByText(/no activity yet/i);
    expect(api.getBoardActivity).toHaveBeenCalledWith(42);
  });
});
