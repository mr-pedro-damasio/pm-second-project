import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import LoginPage from "./page";

describe("LoginPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("renders the login form by default", () => {
    render(<LoginPage />);
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByText(/no account\? create one/i)).toBeInTheDocument();
  });

  it("switches to register mode when the toggle link is clicked", async () => {
    render(<LoginPage />);
    await userEvent.click(screen.getByText(/no account\? create one/i));
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByText(/already have an account/i)).toBeInTheDocument();
  });

  it("switches back to login mode from register mode", async () => {
    render(<LoginPage />);
    await userEvent.click(screen.getByText(/no account\? create one/i));
    await userEvent.click(screen.getByText(/already have an account/i));
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("calls /api/auth/login on login submit", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
    } as Response);
    // Stub window.location
    const assignMock = vi.fn();
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });

    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(fetch).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("calls /api/auth/register on register submit", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 201,
    } as Response);
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });

    render(<LoginPage />);
    await userEvent.click(screen.getByText(/no account\? create one/i));
    await userEvent.type(screen.getByLabelText(/username/i), "newuser");
    await userEvent.type(screen.getByLabelText(/^password/i), "securepass");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(fetch).toHaveBeenCalledWith(
      "/api/auth/register",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("shows error on 401 login response", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({}),
    } as Response);

    render(<LoginPage />);
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/^password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByText(/invalid username or password/i)).toBeInTheDocument();
  });

  it("shows duplicate error on 409 register response", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 409,
      json: () => Promise.resolve({}),
    } as Response);

    render(<LoginPage />);
    await userEvent.click(screen.getByText(/no account\? create one/i));
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/^password/i), "password123");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByText(/username already taken/i)).toBeInTheDocument();
  });
});
