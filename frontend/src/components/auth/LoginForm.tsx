/**
 * Login form component.
 *
 * Handles email/password authentication with validation and error display.
 */

import { useState, type FormEvent } from "react";
import { useAuth } from "../../lib/auth";
import { cn } from "../../lib/utils";

interface LoginFormProps {
  onSuccess?: () => void;
  onRegisterClick?: () => void;
  onForgotPasswordClick?: () => void;
  className?: string;
}

export function LoginForm({
  onSuccess,
  onRegisterClick,
  onForgotPasswordClick,
  className,
}: LoginFormProps) {
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const result = await login(email, password);

    setIsLoading(false);

    if (result.success) {
      onSuccess?.();
    } else {
      setError(result.error || "Login failed");
    }
  };

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-4", className)}>
      <div className="space-y-2">
        <h2 className="text-2xl font-bold tracking-tight">Sign in</h2>
        <p className="text-muted-foreground">
          Enter your credentials to access your account
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            required
            disabled={isLoading}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm
                     focus:outline-none focus:ring-2 focus:ring-ring
                     disabled:opacity-50"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            {onForgotPasswordClick && (
              <button
                type="button"
                onClick={onForgotPasswordClick}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Forgot password?
              </button>
            )}
          </div>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            required
            disabled={isLoading}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm
                     focus:outline-none focus:ring-2 focus:ring-ring
                     disabled:opacity-50"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-2 px-4 rounded-md bg-primary text-primary-foreground
                   font-medium hover:bg-primary/90 disabled:opacity-50
                   focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {isLoading ? "Signing in..." : "Sign in"}
        </button>
      </div>

      {onRegisterClick && (
        <div className="text-center text-sm">
          <span className="text-muted-foreground">Don't have an account? </span>
          <button
            type="button"
            onClick={onRegisterClick}
            className="text-primary hover:underline"
          >
            Sign up
          </button>
        </div>
      )}
    </form>
  );
}
