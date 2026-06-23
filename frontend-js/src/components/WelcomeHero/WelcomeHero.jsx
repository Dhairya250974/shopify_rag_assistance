import { BookOpen, Search, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { SearchBar } from "../SearchBar/SearchBar";

export function WelcomeHero({ examples, isLoading, onAsk }) {
  return (
    <div className="relative mx-auto flex min-h-[calc(100vh-48px)] w-full max-w-5xl flex-col justify-center overflow-hidden px-5 py-20">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-1/2 h-[520px] w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-shopify-500/20 blur-3xl dark:bg-shopify-500/10" />
        <div className="absolute right-8 top-24 h-56 w-56 rounded-full bg-cyan-300/20 blur-3xl dark:bg-cyan-400/10" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="text-center"
      >
        <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-shopify-100 bg-white/80 px-4 py-2 text-sm font-medium text-shopify-700 shadow-sm backdrop-blur dark:border-shopify-500/20 dark:bg-white/5 dark:text-shopify-100">
          <Sparkles className="h-4 w-4" />
          Official-docs grounded answers
        </div>
        <h1 className="mx-auto max-w-4xl text-balance text-4xl font-semibold tracking-tight text-slate-950 sm:text-6xl dark:text-white">
          Shopify Documentation AI Assistant
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-balance text-lg leading-8 text-slate-600 dark:text-slate-300">
          Ask questions about Shopify and receive grounded answers from official documentation.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.08 }}
        className="mx-auto mt-10 w-full max-w-3xl"
      >
        <SearchBar onSubmit={onAsk} isLoading={isLoading} autoFocus placeholder="How do I set up free shipping?" />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.16 }}
        className="mx-auto mt-8 grid w-full max-w-4xl gap-3 sm:grid-cols-2 lg:grid-cols-3"
      >
        {examples.map((question, index) => (
          <button
            key={question}
            type="button"
            onClick={() => onAsk(question)}
            className="group rounded-2xl border border-slate-200 bg-white/80 p-4 text-left shadow-sm backdrop-blur transition hover:-translate-y-0.5 hover:border-shopify-500/60 hover:shadow-soft dark:border-white/10 dark:bg-white/[0.04]"
          >
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-600 transition group-hover:bg-shopify-50 group-hover:text-shopify-700 dark:bg-white/10 dark:text-slate-300 dark:group-hover:bg-shopify-500/10 dark:group-hover:text-shopify-100">
              {index % 2 === 0 ? <Search className="h-4 w-4" /> : <BookOpen className="h-4 w-4" />}
            </div>
            <div className="text-sm font-medium leading-6 text-slate-800 dark:text-slate-100">{question}</div>
          </button>
        ))}
      </motion.div>
    </div>
  );
}
