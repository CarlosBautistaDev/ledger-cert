import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardBody } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Layout } from "@/features/certificates/Layout";
import { useAuth } from "@/features/auth/useAuth";

interface ManagedUser {
  id: number;
  email: string;
  nombre: string;
  activo: boolean;
  roles: string[];
}

interface Role {
  clave: "Elaborador" | "Firmante" | "Auditor" | "Admin";
  nombre_es: string;
  descripcion_es: string;
}

interface Paginated<T> {
  results: T[];
}

const initialForm = {
  nombre: "",
  email: "",
  password: "",
  roles: ["Elaborador"],
};

/** Pantalla para dar de alta cuentas y consultar los roles asignados. */
export function UserManagementPage(): React.ReactElement {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [form, setForm] = React.useState(initialForm);
  const [message, setMessage] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const canManage = Boolean(user?.is_superuser || user?.roles.includes("Admin"));
  const { data: users, isLoading } = useQuery({
    queryKey: ["users"],
    enabled: canManage,
    queryFn: async (): Promise<ManagedUser[]> => {
      const response = await api.get<Paginated<ManagedUser> | ManagedUser[]>("/users/");
      return Array.isArray(response.data) ? response.data : response.data.results;
    },
  });
  const { data: roles = [] } = useQuery({
    queryKey: ["roles"],
    enabled: canManage,
    queryFn: async (): Promise<Role[]> => {
      const response = await api.get<Role[]>("/roles/");
      return response.data.filter((role) => role.clave !== "Admin");
    },
  });

  const submit = async (event: React.FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setMessage(null);
    setError(null);
    try {
      await api.post("/users/", form);
      setForm(initialForm);
      setMessage("Usuario creado.");
      await queryClient.invalidateQueries({ queryKey: ["users"] });
    } catch {
      setError("No se pudo crear. Revisa correo, contraseña y rol.");
    }
  };

  if (!canManage) {
    return (
      <Layout>
        <p className="text-destructive">No tienes permiso para administrar usuarios.</p>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-4">
        <h1 className="text-lg font-semibold">Usuarios y roles</h1>
        <p className="text-sm text-muted-foreground">
          Crea cuentas operativas y asigna un rol segun su funcion.
        </p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <Card>
          <CardBody>
            <form className="space-y-4" onSubmit={submit}>
              <div className="space-y-1">
                <Label htmlFor="nombre">Nombre</Label>
                <Input
                  id="nombre"
                  value={form.nombre}
                  onChange={(event) => setForm({ ...form, nombre: event.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="email">Correo</Label>
                <Input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={(event) => setForm({ ...form, email: event.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="password">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  value={form.password}
                  onChange={(event) => setForm({ ...form, password: event.target.value })}
                  minLength={10}
                  required
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="rol">Rol</Label>
                <select
                  id="rol"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={form.roles[0]}
                  onChange={(event) => setForm({ ...form, roles: [event.target.value] })}
                >
                  {roles.map((role) => (
                    <option key={role.clave} value={role.clave}>
                      {role.nombre_es}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-muted-foreground">
                  {roles.find((role) => role.clave === form.roles[0])?.descripcion_es}
                </p>
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              {message && <p className="text-sm text-muted-foreground">{message}</p>}
              <Button type="submit">Crear usuario</Button>
            </form>
          </CardBody>
        </Card>
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-secondary text-left">
              <tr>
                <th className="px-4 py-2">Nombre</th>
                <th className="px-4 py-2">Correo</th>
                <th className="px-4 py-2">Rol</th>
                <th className="px-4 py-2">Estado</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td className="px-4 py-3 text-muted-foreground" colSpan={4}>Cargando...</td></tr>
              )}
              {users?.map((managedUser) => (
                <tr key={managedUser.id} className="border-t border-border">
                  <td className="px-4 py-2 font-medium">{managedUser.nombre}</td>
                  <td className="px-4 py-2">{managedUser.email}</td>
                  <td className="px-4 py-2">{managedUser.roles.join(", ") || "Sin rol"}</td>
                  <td className="px-4 py-2">{managedUser.activo ? "Activo" : "Inactivo"}</td>
                </tr>
              ))}
              {users?.length === 0 && (
                <tr><td className="px-4 py-3 text-muted-foreground" colSpan={4}>Sin usuarios.</td></tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>
    </Layout>
  );
}
