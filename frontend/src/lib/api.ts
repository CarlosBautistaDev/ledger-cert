import axios from "axios";

/**
 * Axios instance for the Ledger API. Base URL comes from `VITE_API_URL`
 * (defaults to `/api`, resolved by Caddy). A request interceptor attaches the
 * JWT access token from localStorage.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
