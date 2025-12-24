/**
 * Tests for RegisterForm component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RegisterForm } from "./RegisterForm";
import { AuthProvider } from "../../lib/auth";

// Helper to create mock response
function mockResponse(ok: boolean, data: unknown) {
  const text = JSON.stringify(data);
  return {
    ok,
    status: ok ? 200 : 401,
    text: () => Promise.resolve(text),
    json: () => Promise.resolve(data),
  } as Response;
}

function renderRegisterForm(props = {}) {
  vi.mocked(global.fetch).mockResolvedValue(mockResponse(false, {}));

  return render(
    <AuthProvider>
      <RegisterForm {...props} />
    </AuthProvider>
  );
}

describe("RegisterForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders all required fields", async () => {
    renderRegisterForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
  });

  it("shows password requirements hint", async () => {
    renderRegisterForm();

    await waitFor(() => {
      expect(screen.getByText(/8 characters/i)).toBeInTheDocument();
    });
  });

  it("validates password match", async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/^name$/i), "Test User");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "ValidPass123");
    await user.type(screen.getByLabelText(/confirm password/i), "DifferentPass123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
  });

  it("validates password length", async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/^name$/i), "Test User");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "Ab1");
    await user.type(screen.getByLabelText(/confirm password/i), "Ab1");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    // Use exact text to avoid matching the hint text
    await waitFor(() => {
      expect(screen.getByText("Password must be at least 8 characters")).toBeInTheDocument();
    });
  });

  it("validates uppercase requirement", async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/^name$/i), "Test User");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "alllowercase1");
    await user.type(screen.getByLabelText(/confirm password/i), "alllowercase1");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    // Use exact text to avoid matching the hint text
    await waitFor(() => {
      expect(screen.getByText("Password must contain at least one uppercase letter")).toBeInTheDocument();
    });
  });

  it("validates digit requirement", async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/^name$/i), "Test User");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "NoDigitsHere");
    await user.type(screen.getByLabelText(/confirm password/i), "NoDigitsHere");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    // Use exact text to avoid matching the hint text
    await waitFor(() => {
      expect(screen.getByText("Password must contain at least one digit")).toBeInTheDocument();
    });
  });

  it("submits valid registration", async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();

    vi.mocked(global.fetch)
      .mockResolvedValueOnce(mockResponse(false, {}))
      .mockResolvedValueOnce(
        mockResponse(true, {
          access_token: "token",
          expires_in: 900,
          user: { id: "1", email: "test@example.com", name: "Test User" },
        })
      );

    renderRegisterForm({ onSuccess });

    await waitFor(() => {
      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/^name$/i), "Test User");
    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "ValidPass123");
    await user.type(screen.getByLabelText(/confirm password/i), "ValidPass123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it("shows login link when callback provided", async () => {
    const onLoginClick = vi.fn();
    renderRegisterForm({ onLoginClick });

    await waitFor(() => {
      expect(screen.getByText(/sign in/i)).toBeInTheDocument();
    });
  });
});
