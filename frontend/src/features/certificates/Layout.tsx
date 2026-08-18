import * as React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/useAuth";
import { Button } from "@/components/ui/button";

/** Shared page layout with a header and logout. */
export function Layout({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b border-border bg-card px-6 py-3">
        <button
          className="font-semibold"
          onClick={() => navigate("/")}
          type="button"
        >
          Ledger de Certificados
        </button>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-muted-foreground">
            {user?.nombre} {user?.roles?.length ? `(${user.roles.join(", ")})` : ""}
          </span>
          <Button
            variant="outline"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Salir
          </Button>
        </div>
      </header>
      <main className="mx-auto max-w-5xl p-6">{children}</main>
    </div>
  );
}
