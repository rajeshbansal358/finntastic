import type { CheckResponse, Difficulty, HintResponse, RandomSentence } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text();
    if (res.status >= 500 && !text) {
      throw new Error(
        `Backend unreachable (HTTP ${res.status}). Make sure uvicorn is running on port 8000.`,
      );
    }
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

export function fetchRandomSentence(
  difficulty: Difficulty,
  excludeId?: number,
): Promise<RandomSentence> {
  const params = new URLSearchParams({ difficulty });
  if (excludeId !== undefined) {
    params.set("exclude_id", String(excludeId));
  }
  return request<RandomSentence>(`/api/sentences/random?${params.toString()}`);
}

export function fetchHint(
  sentenceId: number,
  wordIndex: number,
  stage: "stem" | "inflection",
): Promise<HintResponse> {
  const params = new URLSearchParams({
    word_index: String(wordIndex),
    stage,
  });
  return request<HintResponse>(`/api/sentences/${sentenceId}/hint?${params.toString()}`);
}

export function checkSentence(sentenceId: number, words: string[]): Promise<CheckResponse> {
  return request<CheckResponse>(`/api/sentences/${sentenceId}/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ words }),
  });
}
