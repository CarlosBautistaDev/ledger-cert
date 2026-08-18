import * as React from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardBody } from "@/components/ui/card";
import { Layout } from "@/features/certificates/Layout";

const schema = z.object({
  codigo: z.string().min(1, "Requerido"),
  asunto: z.string().min(1, "Requerido"),
  emitido_a: z.string().optional(),
  veredicto: z.enum(["CONFORME", "NO_CONFORME"]),
  observaciones: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

/** Create a draft certificate. */
export function CertificateCreatePage(): React.ReactElement {
  const navigate = useNavigate();
  const [error, setError] = React.useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { veredicto: "CONFORME" },
  });

  const onSubmit = async (values: FormValues): Promise<void> => {
    setError(null);
    try {
      const res = await api.post("/ledger/certificates/", values);
      navigate(`/certificates/${res.data.id}`);
    } catch {
      setError("No se pudo crear el certificado (revisa permisos y datos).");
    }
  };

  return (
    <Layout>
      <h1 className="mb-4 text-lg font-semibold">Nuevo certificado</h1>
      <Card className="max-w-xl">
        <CardBody>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1">
              <Label htmlFor="codigo">Código</Label>
              <Input id="codigo" placeholder="CERT-0003" {...register("codigo")} />
              {errors.codigo && (
                <p className="text-xs text-destructive">{errors.codigo.message}</p>
              )}
            </div>
            <div className="space-y-1">
              <Label htmlFor="asunto">Asunto</Label>
              <Input id="asunto" {...register("asunto")} />
              {errors.asunto && (
                <p className="text-xs text-destructive">{errors.asunto.message}</p>
              )}
            </div>
            <div className="space-y-1">
              <Label htmlFor="emitido_a">Emitido a</Label>
              <Input id="emitido_a" {...register("emitido_a")} />
            </div>
            <div className="space-y-1">
              <Label htmlFor="veredicto">Veredicto</Label>
              <select
                id="veredicto"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                {...register("veredicto")}
              >
                <option value="CONFORME">CONFORME</option>
                <option value="NO_CONFORME">NO_CONFORME</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="observaciones">Observaciones</Label>
              <Input id="observaciones" {...register("observaciones")} />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <div className="flex gap-2">
              <Button type="submit" disabled={isSubmitting}>
                Crear borrador
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/")}
              >
                Cancelar
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>
    </Layout>
  );
}
