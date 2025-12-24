/**
 * Authentication context and hooks for braidMgr.
 *
 * Provides:
 * - AuthProvider for wrapping app
 * - useAuth hook for accessing auth state
 * - Auto-refresh of tokens before expiry
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import {
  apiPost,
  setAccessToken,
  clearAccessToken,
} from "./api";

// =============================================================================
// TYPES
// =============================================================================

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  email_verified: boolean;
  org_id?: string;
  org_role?: string;
}

export interface AuthState {
  // State
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  // Actions
  login: (email: string, password: string) => Promise<AuthResult>;
  register: (
    email: string,
    password: string,
    name: string
  ) => Promise<AuthResult>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<{ success: boolean; message: string }>;
  resetPassword: (
    email: string,
    token: string,
    newPassword: string
  ) => Promise<AuthResult>;
}

export interface AuthResult {
  success: boolean;
  error?: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// =============================================================================
// CONTEXT
// =============================================================================

const AuthContext = createContext<AuthState | null>(null);

// =============================================================================
// PROVIDER
// =============================================================================

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Computed state
  const isAuthenticated = user !== null;

  // -------------------------------------------------------------------------
  // Token refresh timer
  // -------------------------------------------------------------------------
  useEffect(() => {
    // Check for existing session on mount
    const checkSession = async () => {
      // Try to refresh token from httpOnly cookie
      const response = await apiPost<AuthResponse>("/auth/refresh");
      if (response.data) {
        setAccessToken(response.data.access_token);
        setUser(response.data.user);
        scheduleRefresh(response.data.expires_in);
      }
      setIsLoading(false);
    };

    checkSession();
  }, []);

  // Schedule token refresh 1 minute before expiry
  const scheduleRefresh = useCallback((expiresIn: number) => {
    const refreshTime = (expiresIn - 60) * 1000; // 1 minute before expiry
    if (refreshTime > 0) {
      setTimeout(async () => {
        const response = await apiPost<AuthResponse>("/auth/refresh");
        if (response.data) {
          setAccessToken(response.data.access_token);
          scheduleRefresh(response.data.expires_in);
        } else {
          // Refresh failed - log out
          setUser(null);
          clearAccessToken();
        }
      }, refreshTime);
    }
  }, []);

  // -------------------------------------------------------------------------
  // Auth actions
  // -------------------------------------------------------------------------

  const login = useCallback(
    async (email: string, password: string): Promise<AuthResult> => {
      const response = await apiPost<AuthResponse>("/auth/login", {
        email,
        password,
      });

      if (response.error) {
        return { success: false, error: response.error.message };
      }

      if (response.data) {
        setAccessToken(response.data.access_token);
        setUser(response.data.user);
        scheduleRefresh(response.data.expires_in);
        return { success: true };
      }

      return { success: false, error: "Unknown error" };
    },
    [scheduleRefresh]
  );

  const register = useCallback(
    async (
      email: string,
      password: string,
      name: string
    ): Promise<AuthResult> => {
      const response = await apiPost<AuthResponse>("/auth/register", {
        email,
        password,
        name,
      });

      if (response.error) {
        return { success: false, error: response.error.message };
      }

      if (response.data) {
        setAccessToken(response.data.access_token);
        setUser(response.data.user);
        scheduleRefresh(response.data.expires_in);
        return { success: true };
      }

      return { success: false, error: "Unknown error" };
    },
    [scheduleRefresh]
  );

  const logout = useCallback(async (): Promise<void> => {
    // Best effort - server will invalidate refresh token cookie
    await apiPost("/auth/logout");
    setUser(null);
    clearAccessToken();
  }, []);

  const forgotPassword = useCallback(
    async (email: string): Promise<{ success: boolean; message: string }> => {
      const response = await apiPost<{ message: string }>("/auth/forgot-password", {
        email,
      });

      if (response.error) {
        return { success: false, message: response.error.message };
      }

      return {
        success: true,
        message: response.data?.message || "Password reset email sent",
      };
    },
    []
  );

  const resetPassword = useCallback(
    async (
      email: string,
      token: string,
      newPassword: string
    ): Promise<AuthResult> => {
      const response = await apiPost<AuthResponse>("/auth/reset-password", {
        email,
        token,
        new_password: newPassword,
      });

      if (response.error) {
        return { success: false, error: response.error.message };
      }

      if (response.data) {
        setAccessToken(response.data.access_token);
        setUser(response.data.user);
        scheduleRefresh(response.data.expires_in);
        return { success: true };
      }

      return { success: false, error: "Unknown error" };
    },
    [scheduleRefresh]
  );

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  const value: AuthState = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// =============================================================================
// HOOKS
// =============================================================================

/**
 * Hook to access auth state and actions.
 *
 * Must be used within AuthProvider.
 */
export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

/**
 * Hook to require authentication.
 *
 * Returns user or null if not authenticated.
 * Use with redirect logic in protected routes.
 */
export function useRequireAuth(): User | null {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  return user;
}
