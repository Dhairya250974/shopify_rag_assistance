import { MessageCircle } from "lucide-react";

export function EmptyState() {
  return (
    <div className="mx-auto mt-12 max-w-md rounded-3xl border border-dashed border-slate-200 bg-white/60 p-8 text-center text-slate-500 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-400">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-shopify-50 text-shopify-700 dark:bg-shopify-500/10 dark:text-shopify-100">
        <MessageCircle className="h-5 w-5" />
      </div>
      <div className="text-sm font-medium text-slate-900 dark:text-white">Start with a Shopify question</div>
      <p className="mt-2 text-sm leading-6">Ask about store setup, payments, shipping, products, refunds, SEO, or customer workflows.</p>
    </div>
  );
}
