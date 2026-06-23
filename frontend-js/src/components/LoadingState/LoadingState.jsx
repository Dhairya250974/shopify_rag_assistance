import { Search, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

export function LoadingState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="mr-auto max-w-3xl"
    >
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.04]">
        <div className="mb-4 flex items-center gap-3 text-sm font-medium text-slate-700 dark:text-slate-200">
          <span className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-shopify-50 text-shopify-700 dark:bg-shopify-500/10 dark:text-shopify-100">
            <Search className="h-4 w-4 animate-pulse" />
          </span>
          Searching Shopify documentation...
        </div>
        <div className="space-y-3">
          <SkeletonLine width="w-11/12" />
          <SkeletonLine width="w-9/12" />
          <SkeletonLine width="w-10/12" />
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <DiscoveryCard label="Retrieving relevant chunks" delay={0} />
          <DiscoveryCard label="Preparing grounded answer" delay={0.15} />
        </div>
      </div>
    </motion.div>
  );
}

function SkeletonLine({ width }) {
  return (
    <div
      className={`${width} h-3 rounded-full bg-[linear-gradient(90deg,#e5e7eb_25%,#f8fafc_50%,#e5e7eb_75%)] bg-[length:200%_100%] animate-shimmer dark:bg-[linear-gradient(90deg,rgba(255,255,255,0.08)_25%,rgba(255,255,255,0.16)_50%,rgba(255,255,255,0.08)_75%)]`}
    />
  );
}

function DiscoveryCard({ label, delay }) {
  return (
    <motion.div
      initial={{ opacity: 0.5 }}
      animate={{ opacity: [0.5, 1, 0.5] }}
      transition={{ repeat: Infinity, duration: 1.8, delay }}
      className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-xs text-slate-500 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-400"
    >
      <Sparkles className="h-3.5 w-3.5 text-shopify-600 dark:text-shopify-100" />
      {label}
    </motion.div>
  );
}
