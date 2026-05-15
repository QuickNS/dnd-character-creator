import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import { queryClient } from "@/lib/queryClient";
import { router } from "./router";
import { UpdatePrompt } from "@/components/UpdatePrompt";
import { OfflineIndicator } from "@/components/OfflineIndicator";

export function Providers() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <UpdatePrompt />
      <OfflineIndicator />
    </QueryClientProvider>
  );
}
