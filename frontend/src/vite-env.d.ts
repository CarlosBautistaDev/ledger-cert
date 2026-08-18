/// <reference types="vite/client" />

/** Typing of the Vite env vars used by the SPA. */
interface ImportMetaEnv {
  /** API base URL (defaults to `/api`, resolved by Caddy/nginx). */
  readonly VITE_API_URL?: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
