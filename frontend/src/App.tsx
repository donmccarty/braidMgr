import { useState } from "react";
import { useAuth } from "./lib/auth";
import { LoginForm, RegisterForm, ForgotPasswordForm } from "./components/auth";

type AuthView = "login" | "register" | "forgot-password";

function App() {
  const { user, isLoading, isAuthenticated, logout } = useAuth();
  const [authView, setAuthView] = useState<AuthView>("login");

  // Show loading state while checking session
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight">braidMgr</h1>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Show auth forms when not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold tracking-tight">braidMgr</h1>
            <p className="text-muted-foreground mt-2">
              Multi-tenant RAID log management
            </p>
          </div>

          <div className="p-6 rounded-lg border bg-card">
            {authView === "login" && (
              <LoginForm
                onSuccess={() => {}}
                onRegisterClick={() => setAuthView("register")}
                onForgotPasswordClick={() => setAuthView("forgot-password")}
              />
            )}

            {authView === "register" && (
              <RegisterForm
                onSuccess={() => {}}
                onLoginClick={() => setAuthView("login")}
              />
            )}

            {authView === "forgot-password" && (
              <ForgotPasswordForm
                onSuccess={() => setAuthView("login")}
                onBackClick={() => setAuthView("login")}
              />
            )}
          </div>
        </div>
      </div>
    );
  }

  // Authenticated view
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">braidMgr</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {user?.name} ({user?.email})
            </span>
            <button
              onClick={logout}
              className="px-3 py-1.5 text-sm rounded-md border hover:bg-accent"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-semibold">Welcome, {user?.name}!</h2>
          <p className="text-muted-foreground">
            You are now authenticated. Dashboard coming soon.
          </p>

          <div className="mt-8 p-6 rounded-lg border bg-card inline-block text-left">
            <h3 className="font-medium mb-2">User Info</h3>
            <dl className="text-sm space-y-1">
              <div className="flex gap-2">
                <dt className="text-muted-foreground">ID:</dt>
                <dd className="font-mono">{user?.id}</dd>
              </div>
              <div className="flex gap-2">
                <dt className="text-muted-foreground">Email:</dt>
                <dd>{user?.email}</dd>
              </div>
              <div className="flex gap-2">
                <dt className="text-muted-foreground">Verified:</dt>
                <dd>{user?.email_verified ? "Yes" : "No"}</dd>
              </div>
            </dl>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
