import { ExternalLink, FileText } from "lucide-react";

function domainFromUrl(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "source";
  }
}

export function SourceCard({ source }) {
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noreferrer"
      className="group flex min-h-[86px] flex-col justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-shopify-500/60 hover:shadow-soft dark:border-white/10 dark:bg-white/[0.04] dark:hover:border-shopify-500/60"
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-shopify-50 text-shopify-700 dark:bg-shopify-500/10 dark:text-shopify-100">
          <FileText className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <div className="line-clamp-2 text-sm font-semibold leading-5 text-slate-900 dark:text-white">
            {source.title}
          </div>
          <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{domainFromUrl(source.url)}</div>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-1 text-xs font-medium text-shopify-700 opacity-80 transition group-hover:opacity-100 dark:text-shopify-100">
        Open source <ExternalLink className="h-3.5 w-3.5" />
      </div>
    </a>
  );
}
