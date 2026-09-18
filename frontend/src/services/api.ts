const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  createConversation: (title?: string) =>
    request<{ id: string; title?: string }>("/api/v1/chat/conversations", {
      method: "POST",
      body: JSON.stringify({ title: title || null }),
    }),

  listConversations: () =>
    request<
      Array<{ id: string; title?: string; created_at: string; updated_at: string }>
    >("/api/v1/chat/conversations"),

  getConversation: (id: string) =>
    request(`/api/v1/chat/conversations/${id}`),

  sendMessage: (conversationId: string, content: string, structured_input?: Record<string, unknown>) =>
    request<{
      conversation_id: string;
      message: unknown;
      response: import("../types").StructuredAIResponse;
    }>(`/api/v1/chat/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, structured_input }),
    }),

  searchKnowledge: (query: string, top_k = 5) =>
    request<{
      query: string;
      count: number;
      results: import("../types").RetrievedChunk[];
    }>("/api/v1/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k }),
    }),

  listSources: () => request("/api/v1/knowledge/sources"),

  analyzeEnvironment: (text: string, variables?: Record<string, unknown>) =>
    request("/api/v1/environment/analyze", {
      method: "POST",
      body: JSON.stringify({ text, variables: variables || {} }),
    }),
};
