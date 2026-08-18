import { Route, Routes, Navigate } from "react-router-dom";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { CertificateListPage } from "@/features/certificates/CertificateListPage";
import { CertificateCreatePage } from "@/features/certificates/CertificateCreatePage";
import { CertificateDetailPage } from "@/features/certificates/CertificateDetailPage";

/** Application routes. */
export function AppRoutes(): React.ReactElement {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route index element={<CertificateListPage />} />
        <Route path="certificates/new" element={<CertificateCreatePage />} />
        <Route path="certificates/:id" element={<CertificateDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
