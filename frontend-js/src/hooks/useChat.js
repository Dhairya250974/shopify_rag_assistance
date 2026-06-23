import { useCallback, useMemo, useState } from "react";
import { askQuestion } from "../services/api";

const RECENTS_KEY = "shopify-rag-recent-questions";

function nowLabel() {
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date());
}

function makeId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function loadRecentQuestions() {
  try {
    const raw = window.localStorage.getItem(RECENTS_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((item) => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function saveRecentQuestions(questions) {
  window.localStorage.setItem(RECENTS_KEY, JSON.stringify(questions.slice(0, 8)));
}

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [recentQuestions, setRecentQuestions] = useState(loadRecentQuestions);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const hasConversation = messages.length > 0;

  const submitQuestion = useCallback(
    async (rawQuestion) => {
      const question = rawQuestion.trim();
      if (!question) {
        setError({
          title: "Ask a question first",
          message: "Type a Shopify question and I will search the documentation for you."
        });
        return;
      }

      if (isLoading) return;

      const userMessage = {
        id: makeId("user"),
        role: "user",
        content: question,
        timestamp: nowLabel()
      };

      setMessages((current) => [...current, userMessage]);
      setError(null);
      setIsLoading(true);

      const nextRecents = [question, ...recentQuestions.filter((item) => item !== question)].slice(0, 8);
      setRecentQuestions(nextRecents);
      saveRecentQuestions(nextRecents);

      try {
        const response = await askQuestion(question);
        const assistantMessage = {
          id: makeId("assistant"),
          role: "assistant",
          content: response.answer,
          timestamp: nowLabel(),
          sources: response.sources,
          latencyMs: response.latency_ms,
          model: response.model,
          chunksUsed: response.chunks_used
        };
        setMessages((current) => [...current, assistantMessage]);
      } catch (caught) {
        const message = caught instanceof Error ? caught.message : "Something went wrong.";
        setError({
          title: "The assistant hit a snag",
          message
        });
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, recentQuestions]
  );

  const startNewChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const deleteRecentQuestion = useCallback((question) => {
    setRecentQuestions((current) => {
      const updated = current.filter((item) => item !== question);
      saveRecentQuestions(updated);
      return updated;
    });
  }, []);

  return useMemo(
    () => ({
      messages,
      recentQuestions,
      isLoading,
      error,
      hasConversation,
      submitQuestion,
      startNewChat,
      deleteRecentQuestion,
      clearError: () => setError(null)
    }),
    [messages, recentQuestions, isLoading, error, hasConversation, submitQuestion, startNewChat, deleteRecentQuestion]
  );
}
