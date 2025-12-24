/**
 * API client for braidMgr backend.
 *
 * Provides typed fetch wrappers with automatic:
 * - Authorization header injection
 * - Token refresh on 401
 * - JSON parsing and error handling
 */

// =============================================================================
// TYPES
// =============================================================================

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
  correlation_id?: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
}

// =============================================================================
// CONFIGURATION
// =============================================================================

const API_BASE_URL = "/api/v1";

// Token storage - in-memory for security (not localStorage)
let accessToken: string | null = null;

// =============================================================================
// TOKEN MANAGEMENT
// =============================================================================

/**
 * Set the current access token.
 * Called after login/register/refresh.
 */
export function setAccessToken(token: string | null): void {
  accessToken = token;
}

/**
 * Get the current access token.
 * Used by auth context to check if logged in.
 */
export function getAccessToken(): string | null {
  return accessToken;
}

/**
 * Clear the access token.
 * Called on logout or auth failure.
 */
export function clearAccessToken(): void {
  accessToken = null;
}

// =============================================================================
// FETCH HELPERS
// =============================================================================

/**
 * Make an authenticated API request.
 *
 * Automatically:
 * - Adds Authorization header if token exists
 * - Parses JSON response
 * - Handles 401 by attempting token refresh
 * - Converts errors to ApiError format
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Add auth header if we have a token
  if (accessToken) {
    (headers as Record<string, string>)["Authorization"] =
      `Bearer ${accessToken}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: "include", // Include cookies for refresh token
    });

    // Handle 401 - try to refresh token
    if (response.status === 401 && accessToken) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        // Retry with new token
        (headers as Record<string, string>)["Authorization"] =
          `Bearer ${accessToken}`;
        const retryResponse = await fetch(url, {
          ...options,
          headers,
          credentials: "include",
        });
        return parseResponse<T>(retryResponse);
      }
      // Refresh failed - clear token and return error
      clearAccessToken();
      return {
        error: {
          error: "authentication_failed",
          message: "Session expired. Please log in again.",
        },
      };
    }

    return parseResponse<T>(response);
  } catch (err) {
    return {
      error: {
        error: "network_error",
        message: err instanceof Error ? err.message : "Network error",
      },
    };
  }
}

/**
 * Parse response body as JSON and handle errors.
 */
async function parseResponse<T>(response: Response): Promise<ApiResponse<T>> {
  // Handle no-content responses
  if (response.status === 204) {
    return { data: undefined as T };
  }

  const text = await response.text();
  let data: T | ApiError;

  try {
    data = JSON.parse(text);
  } catch {
    return {
      error: {
        error: "parse_error",
        message: "Invalid response from server",
      },
    };
  }

  if (!response.ok) {
    return { error: data as ApiError };
  }

  return { data: data as T };
}

/**
 * Attempt to refresh the access token using httpOnly cookie.
 */
async function refreshAccessToken(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    if (data.access_token) {
      accessToken = data.access_token;
      return true;
    }

    return false;
  } catch {
    return false;
  }
}

// =============================================================================
// CONVENIENCE METHODS
// =============================================================================

/**
 * GET request helper.
 */
export async function apiGet<T>(endpoint: string): Promise<ApiResponse<T>> {
  return apiFetch<T>(endpoint, { method: "GET" });
}

/**
 * POST request helper.
 */
export async function apiPost<T>(
  endpoint: string,
  body?: unknown
): Promise<ApiResponse<T>> {
  return apiFetch<T>(endpoint, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * PUT request helper.
 */
export async function apiPut<T>(
  endpoint: string,
  body?: unknown
): Promise<ApiResponse<T>> {
  return apiFetch<T>(endpoint, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * DELETE request helper.
 */
export async function apiDelete<T>(endpoint: string): Promise<ApiResponse<T>> {
  return apiFetch<T>(endpoint, { method: "DELETE" });
}
