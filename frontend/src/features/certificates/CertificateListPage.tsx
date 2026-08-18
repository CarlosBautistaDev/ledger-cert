import * as React from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/features/certificates/Layout";
import type { Certificate, Paginated } from "@/features/certificates/types";

/** List of certificates. */
export function CertificateListPage(): React.ReactElement {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["certificates"],
    queryFn: async (): Promise<Certificate[]> => {
      const res = await api.get<Paginated<Certificate> | Certificate[]>(
        "/ledger/certificates/",
      );
      return Array.isArray(res.data) ? res.data : res.data.results;
    },
  });

  return (
    <Layout>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold">Certificados</h1>
        <Button onClick={() => navigate("/certificates/new")}>
          Nuevo certificado
        </Button>
      </div>
      <Card className="overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary text-left">
            <tr>
              <th className="px-4 py-2">Código</th>
              <th className="px-4 py-2">Asunto</th>
              <th className="px-4 py-2">Veredicto</th>
              <th className="px-4 py-2">Estado</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td className="px-4 py-3 text-muted-foreground" colSpan={4}>
                  Cargando...
                </td>
              </tr>
            )}
            {data?.map((c) => (
              <tr
                key={c.id}
                className="cursor-pointer border-t border-border hover:bg-secondary"
                onClick={() => navigate(`/certificates/${c.id}`)}
              >
                <td className="px-4 py-2 font-medium">{c.codigo}</td>
                <td className="px-4 py-2">{c.asunto}</td>
                <td className="px-4 py-2">{c.veredicto}</td>
                <td className="px-4 py-2">
                  <Badge>{c.estado}</Badge>
                </td>
              </tr>
            ))}
            {data && data.length === 0 && (
              <tr>
                <td className="px-4 py-3 text-muted-foreground" colSpan={4}>
                  Sin registros.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </Layout>
  );
}
