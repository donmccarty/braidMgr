/**
 * Registration form component.
 *
 * Handles new user registration with validation and error display.
 */

import { useState, type FormEvent } from "react";
import { useAuth } from "../../lib/auth";
import { cn } from "../../lib/utils";

interface RegisterFormProps {
  onSuccess?: () => void;
  onLoginClick?: () => void;
  className?: string;
}

export function RegisterForm({
  onSuccess,
  onLoginClick,
  className,
}: RegisterFormProps) {
  const { register } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validation
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    if (!/[A-Z]/.test(password)) {
      setError("Password must contain at least one uppercase letter");
      return;
    }

    if (!/[a-z]/.test(password)) {
      setError("Password must contain at least one lowercase letter");
      return;
    }

    if (!/\d/.test(password)) {
      setError("Password must contain at least one digit");
      return;
    }

    setIsLoading(true);

    const result = await register(email, password, name);

    setIsLoading(false);

    if (result.success) {
      onSuccess?.();
    } else {
      setError(result.error || "Registration failed");
    }
  };

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-4", className)}>
      <div className="space-y-2">
        <h2 className="text-2xl font-bold tracking-tight">Create account</h2>
        <p className="text-muted-foreground">
          Enter your details to create a new account
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="name" className="text-sm font-medium">
            Name
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
            required
            disabled={isLoading}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm
                     focus:outline-none focus:ring-2 focus:ring-ring
                     disabled:opacity-50"
          />
        </div>

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
          <label htmlFor="password" className="text-sm font-medium">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Create a password"
            required
            disabled={isLoading}
            className="w-full px-3 py-2 rounded-md border bg-background text-sm
                     focus:outline-none focus:ring-2 focus:ring-ring
                     disabled:opacity-50"
          />
          <p className="text-xs text-muted-foreground">
            At least 8 characters with uppercase, lowercase, and a digit
          </p>
        </div>

        <div className="space-y-2">
          <label htmlFor="confirmPassword" className="text-sm font-medium">
            Confirm password
          </label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm your password"
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
          {isLoading ? "Creating account..." : "Create account"}
        </button>
      </div>

      {onLoginClick && (
        <div className="text-center text-sm">
          <span className="text-muted-foreground">Already have an account? </span>
          <button
            type="button"
            onClick={onLoginClick}
            className="text-primary hover:underline"
          >
            Sign in
          </button>
        </div>
      )}
    </form>
  );
}
