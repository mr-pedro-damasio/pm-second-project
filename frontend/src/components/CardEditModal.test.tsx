import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { CardEditModal } from "@/components/CardEditModal";

const baseCard = {
  id: "card-1",
  title: "Test Card",
  details: "Some details",
  priority: "medium" as const,
  due_date: null,
  labels: [],
};

describe("CardEditModal", () => {
  it("renders with card values", () => {
    render(<CardEditModal card={baseCard} onSave={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByDisplayValue("Test Card")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Some details")).toBeInTheDocument();
  });

  it("calls onClose when Cancel is clicked", async () => {
    const onClose = vi.fn();
    render(<CardEditModal card={baseCard} onSave={vi.fn()} onClose={onClose} />);
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose when Escape is pressed", async () => {
    const onClose = vi.fn();
    render(<CardEditModal card={baseCard} onSave={vi.fn()} onClose={onClose} />);
    await userEvent.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();
  });

  it("calls onSave with updated title", async () => {
    const onSave = vi.fn();
    render(<CardEditModal card={baseCard} onSave={onSave} onClose={vi.fn()} />);
    const titleInput = screen.getByDisplayValue("Test Card");
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, "Updated Title");
    await userEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ title: "Updated Title" })
    );
  });

  it("Save is disabled when title is empty", async () => {
    render(<CardEditModal card={baseCard} onSave={vi.fn()} onClose={vi.fn()} />);
    const titleInput = screen.getByDisplayValue("Test Card");
    await userEvent.clear(titleInput);
    expect(screen.getByRole("button", { name: /save/i })).toBeDisabled();
  });

  it("adds a label via input and button", async () => {
    const onSave = vi.fn();
    render(<CardEditModal card={baseCard} onSave={onSave} onClose={vi.fn()} />);
    const labelInput = screen.getByPlaceholderText(/add a label/i);
    await userEvent.type(labelInput, "bug");
    await userEvent.click(screen.getByRole("button", { name: /^add$/i }));
    // Label chip should appear
    expect(screen.getByText("bug")).toBeInTheDocument();
    // Save should include the label
    await userEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ labels: ["bug"] })
    );
  });

  it("adds a label via Enter key", async () => {
    render(<CardEditModal card={baseCard} onSave={vi.fn()} onClose={vi.fn()} />);
    const labelInput = screen.getByPlaceholderText(/add a label/i);
    await userEvent.type(labelInput, "feature{Enter}");
    expect(screen.getByText("feature")).toBeInTheDocument();
  });

  it("removes a label when X is clicked", async () => {
    const cardWithLabel = { ...baseCard, labels: ["urgent"] };
    render(<CardEditModal card={cardWithLabel} onSave={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByText("urgent")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /remove label urgent/i }));
    expect(screen.queryByText("urgent")).not.toBeInTheDocument();
  });

  it("renders existing labels from card", () => {
    const cardWithLabels = { ...baseCard, labels: ["backend", "api"] };
    render(<CardEditModal card={cardWithLabels} onSave={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByText("backend")).toBeInTheDocument();
    expect(screen.getByText("api")).toBeInTheDocument();
  });
});
