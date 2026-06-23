import { AlertCircle, X } from "lucide-react";
import { motion } from "framer-motion";

export function ErrorState({ error, onDismiss }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-900 shadow-sm dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-100"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
        <div className="min-w-0 flex-1">
          <div className="font-semibold">{error.title}</div>
          <div className="mt-1 text-sm leading-6 opacity-85">{error.message}</div>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-lg p-1 opacity-70 transition hover:bg-red-100 hover:opacity-100 dark:hover:bg-red-500/20"
          aria-label="Dismiss error"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </motion.div>
  );
}
