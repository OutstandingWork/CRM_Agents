import type {
  AgentInsight,
  DashboardResponse,
  Deal,
  DealDetail,
  RuntimeContext,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001/api";

type RequestOptions = RequestInit & {
  signal?: AbortSignal;
};

async function request<T>(path: string, init?: RequestOptions): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  runtime: (signal?: AbortSignal) => request<RuntimeContext>("/runtime", { signal }),
  dashboard: (signal?: AbortSignal) => request<DashboardResponse>("/dashboard", { signal }),
  deals: (signal?: AbortSignal) => request<Deal[]>("/deals", { signal }),
  dealDetail: (dealId: string, signal?: AbortSignal) => request<DealDetail>(`/deals/${dealId}`, { signal }),
  runAgent: (path: string, dealId: string, signal?: AbortSignal) =>
    request<AgentInsight>(path, {
      method: "POST",
      signal,
      body: JSON.stringify({ deal_id: dealId }),
    }),
  applyAction: (action: AgentInsight["actions"][number]) =>
    request<{ status: string; detail: string; entity_id: string }>("/agents/action/execute", {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
};
