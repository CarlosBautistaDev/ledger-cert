import * as React from "react";
import { api } from "@/lib/api";

/** Authenticated user shape returned by the API. */
export interface AuthUser {
  id: number;
  email: string;
  nombre: string;
  roles: string[];
  is_superuser: boolean;
}

interface AuthContextValue {
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

/** Provider that holds the session (JWT in localStorage) and current user. */
export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const [user, setUser] = React.useState<AuthUser | null>(null);

  React.useEffect(() => {
    const token = localStorage.getItem("access");
    if (!token) {
      return;
    }
    api
      .get<AuthUser>("/auth/me/")
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
      });
  }, []);

  const login = React.useCallback(
    async (email: string, password: string): Promise<void> => {
      const res = await api.post("/auth/login/", { email, password });
      localStorage.setItem("access", res.data.access);
      localStorage.setItem("refresh", res.data.refresh);
      setUser(res.data.user as AuthUser);
    },
    [],
  );

  const logout = React.useCallback((): void => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    setUser(null);
  }, []);

  const value = React.useMemo(
    () => ({ user, login, logout }),
    [user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Access the auth context.
 * @returns the auth context value.
 */
export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  }
  return ctx;
}
