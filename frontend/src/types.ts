export type Difficulty = "easy" | "medium" | "hard";

export type WordStatus =
  | "correct"
  | "mispositioned"
  | "untranslated"
  | "unnecessary"
  | "wrong";

export interface RandomSentence {
  id: number;
  text: string;
  difficulty: Difficulty;
  initial_words: string[];
  target_count: number;
}

export interface HintResponse {
  word_index: number;
  stage: "stem" | "inflection";
  options: string[];
  gradation_note: string | null;
  grammar_note: string | null;
}

export interface WordFeedback {
  index: number;
  word: string;
  status: WordStatus;
  message: string;
}

export interface CheckResponse {
  solved: boolean;
  missing_count: number;
  statuses: WordFeedback[];
}
