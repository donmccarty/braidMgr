/**
 * Tests for ForgotPasswordForm component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ForgotPasswordForm } from "./ForgotPasswordForm";
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

function renderForgotPasswordForm(props = {}) {
  vi.mocked(global.fetch).mockResolvedValue(mockResponse(false, {}));

  return render(
    <AuthProvider>
      <ForgotPasswordForm {...props} />
    </AuthProvider>
  );
}

describe("ForgotPasswordForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders email field", async () => {
    renderForgotPasswordForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });
  });

  it("renders submit button", async () => {
    renderForgotPasswordForm();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /send reset link/i })).toBeInTheDocument();
    });
  });

  it("shows back link when callback provided", async () => {
    const onBackClick = vi.fn();
    renderForgotPasswordForm({ onBackClick });

    await waitFor(() => {
      expect(screen.getByText(/back to sign in/i)).toBeInTheDocument();
    });
  });

  it("calls onBackClick when back link clicked", async () => {
    const user = userEvent.setup();
    const onBackClick = vi.fn();
    renderForgotPasswordForm({ onBackClick });

    await waitFor(() => {
      expect(screen.getByText(/back to sign in/i)).toBeInTheDocument();
    });

    await user.click(screen.getByText(/back to sign in/i));
    expect(onBackClick).toHaveBeenCalled();
  });

  it("shows success message on successful request", async () => {
    const user = userEvent.setup();

    vi.mocked(global.fetch)
      .mockResolvedValueOnce(mockResponse(false, {}))
      .mockResolvedValueOnce(
        mockResponse(true, {
          message: "Password reset email sent",
        })
      );

    renderForgotPasswordForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() => {
      expect(screen.getByText(/password reset email sent/i)).toBeInTheDocument();
    });
  });

  it("shows error on failed request", async () => {
    const user = userEvent.setup();

    vi.mocked(global.fetch)
      .mockResolvedValueOnce(mockResponse(false, {}))
      .mockResolvedValueOnce(
        mockResponse(false, {
          error: "user_not_found",
          message: "No account found with this email",
        })
      );

    renderForgotPasswordForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/email/i), "unknown@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() => {
      expect(screen.getByText(/no account found/i)).toBeInTheDocument();
    });
  });

  it("disables form after success", async () => {
    const user = userEvent.setup();

    vi.mocked(global.fetch)
      .mockResolvedValueOnce(mockResponse(false, {}))
      .mockResolvedValueOnce(
        mockResponse(true, {
          message: "Password reset email sent",
        })
      );

    renderForgotPasswordForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeDisabled();
    });
    expect(screen.getByRole("button", { name: /send reset link/i })).toBeDisabled();
  });
});
