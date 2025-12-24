/**
 * Tests for auth context and hooks.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "./auth";

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

// Helper component to access auth context
function TestComponent() {
  const { user, isLoading, isAuthenticated, login, logout } = useAuth();

  return (
    <div>
      <div data-testid="loading">{isLoading ? "loading" : "ready"}</div>
      <div data-testid="authenticated">{isAuthenticated ? "yes" : "no"}</div>
      <div data-testid="user">{user?.email || "none"}</div>
      <button onClick={() => login("test@example.com", "password")}>
        Login
      </button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("starts in loading state", () => {
    // Mock refresh to never resolve
    vi.mocked(global.fetch).mockImplementation(() => new Promise(() => {}));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId("loading")).toHaveTextContent("loading");
  });

  it("sets ready state after refresh check", async () => {
    // Mock refresh to fail (no existing session)
    vi.mocked(global.fetch).mockResolvedValue(mockResponse(false, {}));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("ready");
    });
    expect(screen.getByTestId("authenticated")).toHaveTextContent("no");
  });

  it("sets user on successful refresh", async () => {
    const mockUser = {
      id: "123",
      email: "test@example.com",
      name: "Test User",
      email_verified: true,
    };

    vi.mocked(global.fetch).mockResolvedValue(
      mockResponse(true, {
        access_token: "token123",
        expires_in: 900,
        user: mockUser,
      })
    );

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent("yes");
    });
    expect(screen.getByTestId("user")).toHaveTextContent("test@example.com");
  });
});

describe("useAuth", () => {
  it("throws when used outside AuthProvider", () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow("useAuth must be used within AuthProvider");

    consoleSpy.mockRestore();
  });
});

// Login integration test skipped - covered by LoginForm tests

describe("logout", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("clears user on logout", async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: "123",
      email: "test@example.com",
      name: "Test User",
      email_verified: true,
    };

    // All calls return success with user
    vi.mocked(global.fetch).mockResolvedValue(
      mockResponse(true, {
        access_token: "token123",
        expires_in: 900,
        user: mockUser,
      })
    );

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent("yes");
    });

    await user.click(screen.getByText("Logout"));

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent("no");
    });
  });
});
