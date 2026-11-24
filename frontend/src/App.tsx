import { useEffect, useState } from "react";
import { checkSentence, fetchRandomSentence } from "./api";
import type { CheckResponse, Difficulty, RandomSentence, WordFeedback } from "./types";

const DIFFICULTIES: Difficulty[] = ["easy", "medium", "hard"];

export function App() {
  const [difficulty, setDifficulty] = useState<Difficulty>("easy");
  const [sentence, setSentence] = useState<RandomSentence | null>(null);
  const [words, setWords] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<CheckResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadSentence(diff: Difficulty, excludeId?: number) {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRandomSentence(diff, excludeId);
      setSentence(data);
      setWords(data.initial_words);
      setSelectedIndex(0);
      setFeedback(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sentence");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSentence(difficulty);
  }, [difficulty]);

  function handleWordChange(index: number, value: string) {
    const next = [...words];
    next[index] = value;
    setWords(next);
    setFeedback(null);
  }

  async function handleCheck() {
    if (!sentence) return;
    setError(null);
    try {
      const result = await checkSentence(sentence.id, words);
      setFeedback(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to check sentence");
    }
  }

  const statusByIndex = new Map<number, WordFeedback>(
    (feedback?.statuses ?? []).map((s) => [s.index, s]),
  );

  return (
    <main className="app">
      <header className="topbar">
        <h1>Finntastic</h1>
        <div className="controls">
          <div className="difficulty-group" role="group" aria-label="Difficulty">
            {DIFFICULTIES.map((d) => (
              <button
                key={d}
                type="button"
                className={difficulty === d ? "active" : ""}
                onClick={() => setDifficulty(d)}
              >
                {d}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => void loadSentence(difficulty, sentence?.id)}
            disabled={loading}
          >
            New sentence
          </button>
        </div>
      </header>

      {error && <p className="error">{error}</p>}

      {sentence && (
        <>
          <section className="prompt-card">
            <div className="meta">
              <span>Difficulty: {sentence.difficulty}</span>
              <span>Target words: ~{sentence.target_count}</span>
            </div>
            <p className="english-text">{sentence.text}</p>
          </section>

          <section className="tiles" aria-label="Word tiles">
            {words.map((word, index) => {
              const fb = statusByIndex.get(index);
              const isSelected = selectedIndex === index;
              return (
                <button
                  key={`${index}-${words.length}`}
                  type="button"
                  className={`tile ${isSelected ? "selected" : ""} ${fb ? `status-${fb.status}` : ""}`}
                  onClick={() => setSelectedIndex(index)}
                >
                  <span className="tile-word">{word || "___"}</span>
                  {fb && <span className="tile-badge">{fb.status}</span>}
                </button>
              );
            })}
          </section>

          {selectedIndex !== null && words[selectedIndex] !== undefined && (
            <section className="editor-card">
              <label className="editor-label" htmlFor="word-input">
                Edit word #{selectedIndex + 1}
              </label>
              <input
                id="word-input"
                type="text"
                value={words[selectedIndex]}
                onChange={(e) => handleWordChange(selectedIndex, e.target.value)}
                placeholder="Type Finnish word..."
              />
              {statusByIndex.get(selectedIndex) && (
                <p className="word-feedback">{statusByIndex.get(selectedIndex)?.message}</p>
              )}
            </section>
          )}

          <section className="submit-bar">
            <button type="button" className="primary" onClick={() => void handleCheck()}>
              Check sentence
            </button>
            {feedback && (
              <p className={feedback.solved ? "solved-msg" : "unsolved-msg"}>
                {feedback.solved
                  ? "Solved! All words and inflections are correct."
                  : `Not quite yet.${feedback.missing_count > 0 ? ` Missing ~${feedback.missing_count} word(s).` : ""}`}
              </p>
            )}
          </section>
        </>
      )}
    </main>
  );
}
