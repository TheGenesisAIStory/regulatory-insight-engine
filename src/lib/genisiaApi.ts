import { AnswerData } from "@/components/AnswerPanel";
import { KnowledgeDoc } from "@/components/DocumentLibrary";

const API_BASE_URL = import.meta.env.VITE_GENISIA_API_URL ?? "http://127.0.0.1:8000";

export interface HealthResponse {
  ready: boolean;
  ollamaOnline: boolean;
  baseDir: string;
  docsDir: string;
  cacheFile: string;
  cacheExists: boolean;
  documents: number;
  chunks: number;
  embedModel: string;
  chatModel: string;
  activeChatModel?: string | null;
  availableModels: string[];
  categories: string[];
  error?: string | null;
}

export interface ReadinessResponse {
  ready: boolean;
  checks: Record<string, boolean>;
  status: HealthResponse;
  reasons: string[];
}

export class GenisiaApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "GenisiaApiError";
    this.status = status;
  }
}

interface ApiDocument {
  id: string;
  title: string;
  source: string;
  pages: number;
  chunks: number;
  status: KnowledgeDoc["status"];
  updated: number;
  filename: string;
}

interface AskResponse extends Omit<AnswerData, "generatedAt"> {
  generatedAt: string;
}

const formatUpdated = (timestamp: number) => {
  if (!timestamp) return "sconosciuto";
  return new Intl.DateTimeFormat("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(timestamp * 1000));
};

const request = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    let message = `Errore API ${response.status}`;
    try {
      const data = await response.json();
      message = data.detail ?? message;
    } catch {
      // Ignore non-JSON error bodies.
    }
    throw new GenisiaApiError(message, response.status);
  }

  return response.json();
};

export const getHealth = () => request<HealthResponse>("/health");
export const getReadiness = () => request<ReadinessResponse>("/ready");

export const getDocuments = async (): Promise<KnowledgeDoc[]> => {
  const data = await request<{ documents: ApiDocument[] }>("/documents");
  return data.documents.map((doc) => ({
    id: doc.id,
    title: doc.title,
    source: doc.source,
    pages: doc.pages,
    chunks: doc.chunks,
    status: doc.status,
    updated: formatUpdated(doc.updated),
  }));
};

export const askGenisia = async (question: string, topK: number, model: string): Promise<AnswerData> => {
  const data = await request<AskResponse>("/ask", {
    method: "POST",
    body: JSON.stringify({ question, topK, model }),
  });

  return {
    ...data,
    generatedAt: new Date(data.generatedAt).toLocaleString("it-IT", {
      dateStyle: "short",
      timeStyle: "short",
    }),
  };
};

export const rebuildIndex = () =>
  request<{ ok: boolean; status: HealthResponse }>("/index/rebuild", {
    method: "POST",
    body: JSON.stringify({ download: true }),
  });

export { API_BASE_URL };
