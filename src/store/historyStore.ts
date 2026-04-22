import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { v4 as uuid } from "uuid";
import type { AnswerData } from "@/components/AnswerPanel";

const TTL_MS = 90 * 24 * 60 * 60 * 1000; // 90 days

export interface HistoryEntry {
  id: string;
  timestamp: number;
  question: string;
  answer: AnswerData;
  tags: string[];
}

interface HistoryState {
  entries: HistoryEntry[];
  addEntry: (question: string, answer: AnswerData) => HistoryEntry;
  removeEntry: (id: string) => void;
  clearAll: () => void;
  pruneExpired: () => void;
}

// Regex matchers for regulatory references → tags
const TAG_PATTERNS: Array<{ re: RegExp; tag: (m: RegExpMatchArray) => string }> = [
  { re: /\bIFRS\s*9\b/gi, tag: () => "IFRS9" },
  { re: /\bBasel\s*(III|IV)\b/gi, tag: (m) => `Basel ${m[1].toUpperCase()}` },
  { re: /\bCRR\s*(?:art\.?|articolo)?\s*(\d{1,4})\b/gi, tag: (m) => `CRR Art. ${m[1]}` },
  { re: /\bart(?:icolo|\.)\s*(\d{1,4})\s*CRR\b/gi, tag: (m) => `CRR Art. ${m[1]}` },
  { re: /\bEBA\/GL\/\d{4}\/\d{1,3}\b/gi, tag: (m) => m[0].toUpperCase() },
  { re: /\bSA-?CCR\b/gi, tag: () => "SA-CCR" },
  { re: /\bFRTB\b/gi, tag: () => "FRTB" },
  { re: /\bECL\b/g, tag: () => "ECL" },
  { re: /\bSICR\b/g, tag: () => "SICR" },
  { re: /\bPOCI\b/g, tag: () => "POCI" },
  { re: /\bNPL\b|\bNPE\b/g, tag: (m) => m[0].toUpperCase() },
];

export const extractTags = (text: string): string[] => {
  const tags = new Set<string>();
  for (const { re, tag } of TAG_PATTERNS) {
    const r = new RegExp(re.source, re.flags);
    let m: RegExpExecArray | null;
    while ((m = r.exec(text)) !== null) {
      tags.add(tag(m));
    }
  }
  return Array.from(tags).slice(0, 6);
};

export const useHistoryStore = create<HistoryState>()(
  persist(
    (set, get) => ({
      entries: [],
      addEntry: (question, answer) => {
        const sourceText = answer.sources.map((s) => `${s.document} ${s.reference}`).join(" ");
        const entry: HistoryEntry = {
          id: uuid(),
          timestamp: Date.now(),
          question,
          answer,
          tags: extractTags(`${question}\n${answer.answer}\n${sourceText}`),
        };
        set({ entries: [entry, ...get().entries] });
        return entry;
      },
      removeEntry: (id) => set({ entries: get().entries.filter((e) => e.id !== id) }),
      clearAll: () => set({ entries: [] }),
      pruneExpired: () => {
        const cutoff = Date.now() - TTL_MS;
        set({ entries: get().entries.filter((e) => e.timestamp >= cutoff) });
      },
    }),
    {
      name: "genisia.history.v1",
      storage: createJSONStorage(() => localStorage),
      onRehydrateStorage: () => (state) => {
        state?.pruneExpired();
      },
    },
  ),
);

// ---------- Date grouping helpers ----------

export type HistoryGroup = "Oggi" | "Ieri" | "Ultimi 7 giorni" | "Più vecchi";

const startOfDay = (d: Date) => {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x.getTime();
};

export const groupOf = (ts: number): HistoryGroup => {
  const today = startOfDay(new Date());
  const yesterday = today - 24 * 60 * 60 * 1000;
  const sevenDays = today - 7 * 24 * 60 * 60 * 1000;
  if (ts >= today) return "Oggi";
  if (ts >= yesterday) return "Ieri";
  if (ts >= sevenDays) return "Ultimi 7 giorni";
  return "Più vecchi";
};

export const todayCount = (entries: HistoryEntry[]) => {
  const today = startOfDay(new Date());
  return entries.filter((e) => e.timestamp >= today).length;
};
