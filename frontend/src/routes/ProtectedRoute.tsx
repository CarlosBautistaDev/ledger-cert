import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/features/auth/useAuth";

/** Guard: redirects to /login when there is no active session. */
export function ProtectedRoute(): React.ReactElement {
  const token = localStorage.getItem("access");
  const { user } = useAuth();
  if (!token && !user) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
