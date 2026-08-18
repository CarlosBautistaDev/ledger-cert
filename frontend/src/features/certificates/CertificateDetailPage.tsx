import * as React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardBody } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/features/certificates/Layout";
import type { Certificate } from "@/features/certificates/types";

/** Certificate detail: shows data and allows signing (Firmante). */
export function CertificateDetailPage(): React.ReactElement {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [password, setPassword] = React.useState("");
  const [msg, setMsg] = React.useState<string | null>(null);

  const { data: cert, isLoading } = useQuery({
    queryKey: ["certificate", id],
    queryFn: async (): Promise<Certificate> => {
      const res = await api.get<Certificate>(`/ledger/certificates/${id}/`);
      return res.data;
    },
  });

  const sign = async (): Promise<void> => {
    setMsg(null);
    try {
      await api.post(`/ledger/certificates/${id}/sign/`, { password });
      setPassword("");
      await qc.invalidateQueries({ queryKey: ["certificate", id] });
    } catch {
      setMsg("No se pudo firmar (revisa rol Firmante y contraseña).");
    }
  };

  if (isLoading || !cert) {
    return (
      <Layout>
        <p className="text-muted-foreground">Cargando...</p>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-lg font-semibold">{cert.codigo}</h1>
        <Badge>{cert.estado}</Badge>
      </div>
      <Card className="max-w-xl">
        <CardBody className="space-y-3 text-sm">
          <div>
            <span className="text-muted-foreground">Asunto: </span>
            {cert.asunto}
          </div>
          <div>
            <span className="text-muted-foreground">Emitido a: </span>
            {cert.emitido_a || "—"}
          </div>
          <div>
            <span className="text-muted-foreground">Veredicto: </span>
            {cert.veredicto}
          </div>
          <div>
            <span className="text-muted-foreground">Observaciones: </span>
            {cert.observaciones || "—"}
          </div>
          {cert.firmada && (
            <div className="break-all">
              <span className="text-muted-foreground">Hash de firma: </span>
              <code className="text-xs">{cert.firma_hash}</code>
            </div>
          )}

          {!cert.firmada ? (
            <div className="space-y-2 border-t border-border pt-3">
              <p className="text-muted-foreground">
                Firmar requiere re-autenticación. Al firmar, el registro queda
                inmutable (la corrección es por supersesión).
              </p>
              <Label htmlFor="pwd">Contraseña</Label>
              <Input
                id="pwd"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <Button onClick={sign} disabled={!password}>
                Firmar
              </Button>
            </div>
          ) : (
            <div className="border-t border-border pt-3">
              <Button variant="outline" disabled title="No disponible">
                Corregir (supersesión)
              </Button>
            </div>
          )}

          {msg && <p className="text-destructive">{msg}</p>}

          <div className="border-t border-border pt-3">
            <Button variant="outline" onClick={() => navigate("/")}>
              Volver
            </Button>
          </div>
        </CardBody>
      </Card>
    </Layout>
  );
}
