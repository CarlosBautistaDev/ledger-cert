/** Certificate shape returned by the API. */
export interface Certificate {
  id: number;
  codigo: string;
  asunto: string;
  emitido_a: string;
  veredicto: "CONFORME" | "NO_CONFORME";
  observaciones: string;
  estado: "BORRADOR" | "FIRMADO" | "REEMPLAZADO";
  firmada: boolean;
  firma_ts: string | null;
  firma_hash: string;
  created_at: string;
}

/** Paginated list response. */
export interface Paginated<T> {
  count: number;
  results: T[];
}
