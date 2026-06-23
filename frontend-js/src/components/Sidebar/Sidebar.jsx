import { MessageSquarePlus, PanelLeftClose, PanelLeftOpen, Search, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { ThemeToggle } from "../ThemeToggle/ThemeToggle";

export function Sidebar({
  examples,
  recentQuestions,
  isDark,
  isOpen,
  onToggleTheme,
  onNewChat,
  onAsk,
  onToggleSidebar
}) {
  return (
    <>
      <button
        type="button"
        onClick={onToggleSidebar}
        className="fixed left-4 top-4 z-40 inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-soft lg:hidden dark:border-white/10 dark:bg-ink-900 dark:text-slate-200"
        aria-label="Toggle sidebar"
      >
        {isOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
      </button>

      {isOpen ? (
        <button
          type="button"
          onClick={onToggleSidebar}
          className="fixed inset-0 z-20 bg-slate-950/30 backdrop-blur-sm lg:hidden"
          aria-label="Close sidebar overlay"
        />
      ) : null}

      <motion.aside
        initial={false}
        animate={{ x: isOpen ? 0 : -320 }}
        transition={{ type: "spring", stiffness: 320, damping: 34 }}
        className="fixed inset-y-0 left-0 z-30 flex w-80 flex-col border-r border-slate-200/80 bg-white/90 px-4 py-5 shadow-soft backdrop-blur-xl lg:static lg:translate-x-0 dark:border-white/10 dark:bg-ink-950/90"
      >
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-shopify-500 text-white shadow-glow">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-950 dark:text-white">Shopify RAG</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">Documentation AI</div>
            </div>
          </div>
          <ThemeToggle isDark={isDark} onToggle={onToggleTheme} />
        </div>

        <button
          type="button"
          onClick={onNewChat}
          className="mb-6 inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-100"
        >
          <MessageSquarePlus className="h-4 w-4" />
          New Chat
        </button>

        <nav className="min-h-0 flex-1 space-y-7 overflow-y-auto pr-1">
          <QuestionGroup
            title="Recent Questions"
            empty="Your recent questions will appear here."
            icon={<Search className="h-4 w-4" />}
            questions={recentQuestions}
            onAsk={onAsk}
          />
          <QuestionGroup
            title="Example Questions"
            icon={<Sparkles className="h-4 w-4" />}
            questions={examples}
            onAsk={onAsk}
          />
        </nav>

        <div className="mt-6 rounded-2xl border border-shopify-100 bg-shopify-50/80 p-4 text-xs leading-5 text-shopify-700 dark:border-shopify-500/20 dark:bg-shopify-500/10 dark:text-shopify-100">
          Answers are grounded in indexed Shopify Help Center chunks and include source cards when available.
        </div>
      </motion.aside>
    </>
  );
}

function QuestionGroup({
  title,
  icon,
  questions,
  empty,
  onAsk
}) {
  return (
    <section>
      <div className="mb-3 flex items-center gap-2 px-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-400 dark:text-slate-500">
        {icon}
        {title}
      </div>
      {questions.length ? (
        <div className="space-y-1.5">
          {questions.map((question) => (
            <button
              key={question}
              type="button"
              onClick={() => onAsk(question)}
              className="w-full rounded-xl px-3 py-2.5 text-left text-sm leading-5 text-slate-700 transition hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-white/[0.07] dark:hover:text-white"
            >
              {question}
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-slate-200 px-3 py-4 text-sm text-slate-400 dark:border-white/10 dark:text-slate-500">
          {empty}
        </div>
      )}
    </section>
  );
}
