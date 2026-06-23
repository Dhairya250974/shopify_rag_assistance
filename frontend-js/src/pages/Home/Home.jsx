import { useEffect, useState } from "react";
import { Sidebar } from "../../components/Sidebar/Sidebar";
import { WelcomeHero } from "../../components/WelcomeHero/WelcomeHero";
import { ChatWindow } from "../../components/ChatWindow/ChatWindow";
import { useChat } from "../../hooks/useChat";

const EXAMPLE_QUESTIONS = [
  "How do I set up free shipping?",
  "How do I process refunds?",
  "How can I improve store SEO?",
  "How do I add product variants?",
  "How do abandoned carts work?",
  "How do Shopify payments work?"
];

export function Home({ isDark, backendDetected, onToggleTheme }) {
  const {
    messages,
    recentQuestions,
    isLoading,
    error,
    hasConversation,
    submitQuestion,
    startNewChat,
    clearError,
    deleteRecentQuestion
  } = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(() => window.matchMedia("(min-width: 1024px)").matches);

  useEffect(() => {
    const media = window.matchMedia("(min-width: 1024px)");
    const syncSidebar = () => setSidebarOpen(media.matches);
    media.addEventListener("change", syncSidebar);
    return () => media.removeEventListener("change", syncSidebar);
  }, []);

  function handleAsk(question) {
    submitQuestion(question);
    if (window.innerWidth < 1024) setSidebarOpen(false);
  }

  function handleDeleteRecent(question) {
    if (typeof deleteRecentQuestion === "function") {
      deleteRecentQuestion(question);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950 transition-colors duration-300 dark:bg-ink-950 dark:text-white">
      <div className="flex min-h-screen">
        <Sidebar
          examples={[]}
          recentQuestions={recentQuestions}
          isDark={isDark}
          isOpen={sidebarOpen}
          onToggleTheme={onToggleTheme}
          onNewChat={startNewChat}
          onAsk={handleAsk}
          onDelete={handleDeleteRecent}
          onToggleSidebar={() => setSidebarOpen((open) => !open)}
        />

        {!backendDetected ? (
          <div className="fixed left-4 right-4 top-4 z-50 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900 shadow-soft lg:left-96 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-100">
            ⚠️ Backend not detected. Answers won't load until the server is running.
          </div>
        ) : null}

        {hasConversation ? (
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            error={error}
            onAsk={handleAsk}
            onDismissError={clearError}
          />
        ) : (
          <main className="min-h-screen flex-1 bg-slate-50 dark:bg-ink-950">
            <WelcomeHero examples={EXAMPLE_QUESTIONS} isLoading={isLoading} onAsk={handleAsk} />
            {error ? (
              <div className="fixed bottom-6 left-4 right-4 mx-auto max-w-2xl lg:left-80">
                <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-900 shadow-soft dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-100">
                  <strong>{error.title}</strong>
                  <p className="mt-1">{error.message}</p>
                </div>
              </div>
            ) : null}
          </main>
        )}
      </div>
    </div>
  );
}
