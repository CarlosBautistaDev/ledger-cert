import * as React from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/features/auth/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardBody } from "@/components/ui/card";

const schema = z.object({
  email: z.string().email("Correo inválido"),
  password: z.string().min(1, "Requerido"),
});
type FormValues = z.infer<typeof schema>;

/** Login page. */
export function LoginPage(): React.ReactElement {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = React.useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues): Promise<void> => {
    setError(null);
    try {
      await login(values.email, values.password);
      navigate("/");
    } catch {
      setError("Credenciales inválidas o cuenta bloqueada.");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardBody className="space-y-4">
          <div>
            <h1 className="text-xl font-semibold">Ledger de Certificados</h1>
            <p className="text-sm text-muted-foreground">
              Inicia sesión para continuar.
            </p>
          </div>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-1">
              <Label htmlFor="email">Correo</Label>
              <Input id="email" type="email" {...register("email")} />
              {errors.email && (
                <p className="text-xs text-destructive">{errors.email.message}</p>
              )}
            </div>
            <div className="space-y-1">
              <Label htmlFor="password">Contraseña</Label>
              <Input id="password" type="password" {...register("password")} />
              {errors.password && (
                <p className="text-xs text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              Entrar
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
