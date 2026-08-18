import { QueryClient } from "@tanstack/react-query";

/** Shared React Query client. */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});
