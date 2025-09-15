import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Provider as JotaiProvider } from "jotai";

export function withProviders(node: React.ReactNode) {
  const client = new QueryClient();
  return (
    <QueryClientProvider client={client}>
      <JotaiProvider>{node}</JotaiProvider>
    </QueryClientProvider>
  );
}

export function renderWithProviders(
  renderImpl: (ui: React.ReactNode) => ReturnType<any>,
  ui: React.ReactNode,
) {
  return renderImpl(withProviders(ui));
}
