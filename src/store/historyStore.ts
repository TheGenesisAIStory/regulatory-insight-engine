import { create } from "zustand";
import type { AnswerData } from "@/components/AnswerPanel";
import { supabase } from "@/integrations/supabase/client";
import type { Json } from "@/integrations/supabase/types";

export interface HistoryEntry {
  id: string;
  timestamp: number;
  question: string;
  answer: AnswerData;
  tags: string[];
}

interface HistoryState {
  entries: HistoryEntry[];
  loading: boolean;
  loadForUser: (userId: string | null) => Promise<void>;
  addEntry: (question: string, answer: AnswerData) => HistoryEntry;
  removeEntry: (id: string) => Promise<void>;
  clearAll: () => Promise<void>;
  reset: () => void;
}

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
    while ((m = r.exec(text)) !== null) tags.add(tag(m));
  }
  return Array.from(tags).slice(0, 6);
};

export const useHistoryStore = create<HistoryState>()((set, get) => ({
  entries: [],
  loading: false,
  reset: () => set({ entries: [], loading: false }),

  loadForUser: async (userId) => {
    if (!userId) {
      set({ entries: [], loading: false });
      return;
    }
    set({ loading: true });
    const { data, error } = await supabase
      .from("conversations")
      .select("id, question, answer, tags, created_at")
      .order("created_at", { ascending: false })
      .limit(200);
    if (error) {
      set({ loading: false });
      return;
    }
    const entries: HistoryEntry[] = (data ?? []).map((row) => ({
      id: row.id,
      question: row.question,
      answer: row.answer as unknown as AnswerData,
      tags: row.tags ?? [],
      timestamp: new Date(row.created_at).getTime(),
    }));
    set({ entries, loading: false });
  },

  addEntry: (question, answer) => {
    const sourceText = answer.sources.map((s) => `${s.document} ${s.reference}`).join(" ");
    const tags = extractTags(`${question}\n${answer.answer}\n${sourceText}`);
    const id = crypto.randomUUID();
    const entry: HistoryEntry = { id, question, answer, tags, timestamp: Date.now() };
    set({ entries: [entry, ...get().entries] });

    // Fire-and-forget DB insert
    void (async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;
      await supabase.from("conversations").insert({
        id,
        user_id: user.id,
        question,
        answer: answer as unknown as Json,
        tags,
      });
    })();

    return entry;
  },

  removeEntry: async (id) => {
    set({ entries: get().entries.filter((e) => e.id !== id) });
    await supabase.from("conversations").delete().eq("id", id);
  },

  clearAll: async () => {
    const ids = get().entries.map((e) => e.id);
    set({ entries: [] });
    if (ids.length > 0) {
      await supabase.from("conversations").delete().in("id", ids);
    }
  },
}));

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
