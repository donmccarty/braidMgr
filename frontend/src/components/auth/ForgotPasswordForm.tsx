/**
 * Forgot password form component.
 *
 * Handles password reset request.
 */

import { useState, type FormEvent } from "react";
import { useAuth } from "../../lib/auth";
import { cn } from "../../lib/utils";

interface ForgotPasswordFormProps {
  onSuccess?: () => void;
  onBackClick?: () => void;
  className?: string;
}

export function ForgotPasswordForm({
  onSuccess,
  onBackClick,
  className,
}: ForgotPasswordFormProps) {
  const { forgotPassword } = useAuth();

  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setIsLoading(true);

    const result = await forgotPassword(email);

    setIsLoading(false);

    if (result.success) {
      setMessage(result.message);
      onSuccess?.();
    } else {
      setError(result.message);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-4", className)}>
      <div className="space-y-2">
        <h2 className="text-2xl font-bold tracking-tight">Reset password</h2>
        <p className="text-muted-foreground">
          Enter your email address and we'll send you a password reset link
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
          {error}
        </div>
      )}

      {message && (
        <div className="p-3 rounded-md bg-green-500/10 text-green-700 text-sm">
          {message}
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
            disabled={isLoading || !!message}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm
                     focus:outline-none focus:ring-2 focus:ring-ring
                     disabled:opacity-50"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !!message}
          className="w-full py-2 px-4 rounded-md bg-primary text-primary-foreground
                   font-medium hover:bg-primary/90 disabled:opacity-50
                   focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {isLoading ? "Sending..." : "Send reset link"}
        </button>
      </div>

      {onBackClick && (
        <div className="text-center text-sm">
          <button
            type="button"
            onClick={onBackClick}
            className="text-muted-foreground hover:text-foreground"
          >
            Back to sign in
          </button>
        </div>
      )}
    </form>
  );
}
