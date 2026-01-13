import axios from "axios";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: apiUrl,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const role = typeof window !== "undefined" ? localStorage.getItem("user_role") : "analyst";
  if (role) {
    config.headers["X-Role"] = role;
  }
  return config;
});

export interface SentimentStats {
  positive: number;
  neutral: number;
  negative: number;
  total: number;
  updated_at: string;
}

export async function fetchSentimentStats() {
  const { data } = await apiClient.get<SentimentStats>("/sentiment/stats");
  return data;
}

export async function fetchDashboardOverview() {
  const [statsRes, trendRes, keywordsRes, sourcesRes] = await Promise.all([
    apiClient.get("/sentiment/stats"),
    apiClient.get("/sentiment/trend", { params: { time_range: "7d" } }),
    apiClient.get("/sentiment/keywords", { params: { limit: 20 } }),
    apiClient.get("/reports/overview"),
  ]);
  return {
    stats: statsRes.data,
    trend: trendRes.data,
    keywords: keywordsRes.data,
    overview: sourcesRes.data,
  };
}

export async function fetchUsers() {
  const { data } = await apiClient.get("/users");
  return data;
}

export async function fetchSources() {
  const { data } = await apiClient.get("/sources");
  return data;
}

export interface CreateSourcePayload {
  name: string;
  type: string;
  config: Record<string, string>;
  status?: string;
  schedule?: string;
}

export async function createSource(payload: CreateSourcePayload) {
  const { data } = await apiClient.post("/sources", payload);
  return data;
}

export async function fetchContents(params?: Record<string, string | number | undefined>) {
  const { data } = await apiClient.get("/contents", { params });
  return data;
}

export async function fetchContentHistory(id: string) {
  const { data } = await apiClient.get(`/contents/${id}/history`);
  return data;
}

export async function updateContentLabel(id: string, label: string) {
  const { data } = await apiClient.patch(`/contents/${id}/label`, { label });
  return data;
}

export async function fetchBrandSentiment(label: string) {
  const { data } = await apiClient.get("/contents/brand", { params: { label } });
  return data;
}

export async function fetchReports() {
  const { data } = await apiClient.get("/reports/overview");
  return data;
}

export async function reloadSources() {
  const { data } = await apiClient.post("/sources/reload");
  return data;
}

export async function uploadTwitterCsv(file: File, limit?: number) {
  const formData = new FormData();
  formData.append("file", file);
  if (limit) {
    formData.append("limit", String(limit));
  }
  const { data } = await apiClient.post("/sources/import/twitter-csv", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function runSentiment(batchLimit?: number) {
  const { data } = await apiClient.post("/sentiment/run", batchLimit ? { batch_limit: batchLimit } : undefined);
  return data;
}

export async function runSentimentForItem(id: string) {
  const { data } = await apiClient.post(`/sentiment/run/${id}`);
  return data;
}

export async function fetchKeywordSentiment(keyword: string, refresh = false) {
  const { data } = await apiClient.get("/sentiment/keyword-stats", { params: { keyword, refresh } });
  return data;
}

export async function fetchBranding() {
  const [branding, template] = await Promise.all([
    apiClient.get("/branding"),
    apiClient.get("/branding/template"),
  ]);
  return { branding: branding.data, template: template.data };
}

export async function fetchSystemStatus() {
  const [status, logs, version] = await Promise.all([
    apiClient.get("/system/status"),
    apiClient.get("/system/logs"),
    apiClient.get("/system/version"),
  ]);
  return { status: status.data, logs: logs.data, version: version.data };
}
