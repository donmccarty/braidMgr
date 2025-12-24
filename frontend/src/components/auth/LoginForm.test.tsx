/**
 * Tests for LoginForm component.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "./LoginForm";
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

// Wrap component with AuthProvider for testing
function renderLoginForm(props = {}) {
  // Mock refresh to fail (no session)
  vi.mocked(global.fetch).mockResolvedValue(mockResponse(false, {}));

  return render(
    <AuthProvider>
      <LoginForm {...props} />
    </AuthProvider>
  );
}

describe("LoginForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders email and password fields", async () => {
    renderLoginForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("renders sign in button", async () => {
    renderLoginForm();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    });
  });

  it("shows register link when callback provided", async () => {
    const onRegisterClick = vi.fn();
    renderLoginForm({ onRegisterClick });

    await waitFor(() => {
      expect(screen.getByText(/sign up/i)).toBeInTheDocument();
    });
  });

  it("shows forgot password link when callback provided", async () => {
    const onForgotPasswordClick = vi.fn();
    renderLoginForm({ onForgotPasswordClick });

    await waitFor(() => {
      expect(screen.getByText(/forgot password/i)).toBeInTheDocument();
    });
  });

  it("calls onRegisterClick when register link clicked", async () => {
    const user = userEvent.setup();
    const onRegisterClick = vi.fn();
    renderLoginForm({ onRegisterClick });

    await waitFor(() => {
      expect(screen.getByText(/sign up/i)).toBeInTheDocument();
    });

    await user.click(screen.getByText(/sign up/i));
    expect(onRegisterClick).toHaveBeenCalled();
  });

  it("submits form with email and password", async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();

    const mockUser = { id: "1", email: "test@example.com", name: "Test" };

    // Mock refresh fail, then login success
    vi.mocked(global.fetch)
      .mockResolvedValueOnce(mockResponse(false, {}))
      .mockResolvedValueOnce(
        mockResponse(true, {
          access_token: "token",
          expires_in: 900,
          user: mockUser,
        })
      );

    renderLoginForm({ onSuccess });

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it("shows error on failed login", async () => {
    const user = userEvent.setup();

    // Mock refresh fail, then login fail
    vi.mocked(global.fetch)
      .mockResolvedValueOnce(mockResponse(false, {}))
      .mockResolvedValueOnce(
        mockResponse(false, {
          error: "invalid_credentials",
          message: "Invalid email or password",
        })
      );

    renderLoginForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/password/i), "wrongpassword");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    // Should show some error (message varies based on API response parsing)
    await waitFor(() => {
      expect(screen.getByText(/failed|invalid|error/i)).toBeInTheDocument();
    });
  });
});
