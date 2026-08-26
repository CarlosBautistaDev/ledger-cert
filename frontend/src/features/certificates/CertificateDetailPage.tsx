import * as React from "react";
import type { AxiosError } from "axios";
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
  const [corrigiendo, setCorrigiendo] = React.useState(false);
  const [correccion, setCorreccion] = React.useState({
    codigo: "",
    asunto: "",
    emitido_a: "",
    veredicto: "CONFORME" as Certificate["veredicto"],
    observaciones: "",
    password: "",
  });

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
    } catch (error) {
      const detail = (error as AxiosError<{ detail?: string }>).response?.data
        ?.detail;
      setMsg(detail ?? "No se pudo firmar. Intenta otra vez.");
    }
  };

  const abrirCorreccion = (): void => {
    setCorreccion({
      codigo: `${cert?.codigo ?? ""}-R1`,
      asunto: cert?.asunto ?? "",
      emitido_a: cert?.emitido_a ?? "",
      veredicto: cert?.veredicto ?? "CONFORME",
      observaciones: cert?.observaciones ?? "",
      password: "",
    });
    setCorrigiendo(true);
    setMsg(null);
  };

  const corregir = async (): Promise<void> => {
    setMsg(null);
    try {
      const res = await api.post<Certificate>(
        `/ledger/certificates/${id}/supersede/`,
        correccion,
      );
      await qc.invalidateQueries({ queryKey: ["certificates"] });
      navigate(`/certificates/${res.data.id}`);
    } catch (error) {
      const detail = (error as AxiosError<{ detail?: string }>).response?.data
        ?.detail;
      setMsg(detail ?? "No se pudo corregir. Intenta otra vez.");
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
          {cert.firmada && !cert.esta_vigente && (
            <p className="text-muted-foreground">
              Este certificado ya fue reemplazado por una corrección.
            </p>
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
              <Button
                variant="outline"
                onClick={abrirCorreccion}
                disabled={!cert.esta_vigente}
              >
                Corregir (supersesión)
              </Button>
            </div>
          )}

          {corrigiendo && (
            <div className="space-y-3 border-t border-border pt-3">
              <p className="text-muted-foreground">
                Se va a emitir un certificado nuevo y el actual queda como historial.
              </p>
              <div className="space-y-1">
                <Label htmlFor="correccion-codigo">Código nuevo</Label>
                <Input
                  id="correccion-codigo"
                  value={correccion.codigo}
                  onChange={(e) => setCorreccion({ ...correccion, codigo: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="correccion-asunto">Asunto</Label>
                <Input
                  id="correccion-asunto"
                  value={correccion.asunto}
                  onChange={(e) => setCorreccion({ ...correccion, asunto: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="correccion-emisor">Emitido a</Label>
                <Input
                  id="correccion-emisor"
                  value={correccion.emitido_a}
                  onChange={(e) => setCorreccion({ ...correccion, emitido_a: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="correccion-veredicto">Veredicto</Label>
                <select
                  id="correccion-veredicto"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={correccion.veredicto}
                  onChange={(e) => setCorreccion({
                    ...correccion,
                    veredicto: e.target.value as Certificate["veredicto"],
                  })}
                >
                  <option value="CONFORME">CONFORME</option>
                  <option value="NO_CONFORME">NO CONFORME</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="correccion-observaciones">Observaciones</Label>
                <Input
                  id="correccion-observaciones"
                  value={correccion.observaciones}
                  onChange={(e) => setCorreccion({ ...correccion, observaciones: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="correccion-password">Contraseña para firmar</Label>
                <Input
                  id="correccion-password"
                  type="password"
                  value={correccion.password}
                  onChange={(e) => setCorreccion({ ...correccion, password: e.target.value })}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={corregir} disabled={!correccion.password}>
                  Emitir corrección
                </Button>
                <Button variant="outline" onClick={() => setCorrigiendo(false)}>
                  Cancelar
                </Button>
              </div>
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
