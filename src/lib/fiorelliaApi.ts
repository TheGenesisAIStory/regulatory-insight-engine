import type { AnswerData } from "@/components/AnswerPanel";

export interface FiorelliaResponse {
  answer: string;
  confidence: number;   // 0..1
  abstention: number;   // 0..1
  sources: { title: string; link: string }[];
}

export const isFiorelliaConfigured = (): boolean =>
  Boolean(import.meta.env.VITE_FIORELLIA_ENDPOINT && import.meta.env.VITE_FIORELLIA_API_KEY);

export const askFiorellIA = async (question: string): Promise<FiorelliaResponse> => {
  const endpoint = import.meta.env.VITE_FIORELLIA_ENDPOINT as string | undefined;
  const apiKey = import.meta.env.VITE_FIORELLIA_API_KEY as string | undefined;
  if (!endpoint || !apiKey) {
    throw new Error("Fiorell.IA non configurata (VITE_FIORELLIA_ENDPOINT / VITE_FIORELLIA_API_KEY).");
  }

  const resp = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json", "api-key": apiKey },
    body: JSON.stringify({ question }),
  });

  if (!resp.ok) throw new Error(`Errore Fiorell.IA ${resp.status}`);
  return (await resp.json()) as FiorelliaResponse;
};

// Map numeric confidence to existing categorical tier
const tierOf = (confidence: number, abstention: number): AnswerData["confidence"] => {
  if (abstention >= 0.5) return "low";
  if (confidence >= 0.75) return "high";
  if (confidence >= 0.45) return "medium";
  return "low";
};

export const toAnswerData = (question: string, r: FiorelliaResponse): AnswerData => {
  const abstain = r.abstention >= 0.5;
  return {
    question,
    answer: r.answer,
    confidence: tierOf(r.confidence, r.abstention),
    confidenceScore: r.confidence,
    abstentionScore: r.abstention,
    noAnswer: abstain,
    reason: abstain ? "Astensione del modello: contesto insufficiente." : null,
    model: "fiorell.ia",
    generatedAt: new Date().toLocaleString("it-IT"),
    sources: r.sources.map((s, i) => ({
      id: `fia-${i}`,
      document: s.title,
      reference: s.link,
      page: 0,
      score: r.confidence,
      excerpt: s.link,
    })),
  };
};
