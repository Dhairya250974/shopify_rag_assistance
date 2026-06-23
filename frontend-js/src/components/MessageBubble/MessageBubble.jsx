import { Check, Copy } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SourceCard } from "../SourceCard/SourceCard";

function highlightCitations(text) {
  if (!text) return text;
  return text.replace(
    /\[Source:\s*([^\]]+)\]/g,
    '<span class="citation-badge">[$1]</span>'
  );
}

export function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  async function copyAnswer() {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <>
      <style>{`
        .citation-badge {
          display: inline-block;
          background-color: #e8f4e8;
          color: #2d6a2d;
          border: 1px solid #a8d5a8;
          border-radius: 4px;
          padding: 1px 7px;
          font-size: 0.78em;
          font-weight: 600;
          margin: 0 3px;
          vertical-align: middle;
          white-space: nowrap;
          font-family: inherit;
        }
        .dark .citation-badge {
          background-color: rgba(150, 191, 72, 0.15);
          color: #96bf48;
          border-color: rgba(150, 191, 72, 0.3);
        }
      `}</style>
      <motion.article
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.24 }}
        className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      >
      <div className={`max-w-[min(820px,100%)] ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        <div
          className={
            isUser
              ? "rounded-3xl rounded-br-lg bg-slate-950 px-5 py-3 text-[15px] leading-7 text-white shadow-sm dark:bg-white dark:text-slate-950"
              : "rounded-3xl rounded-bl-lg border border-slate-200 bg-white px-5 py-4 text-slate-900 shadow-sm dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-100"
          }
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-slate max-w-none prose-p:leading-7 prose-a:text-shopify-700 prose-code:rounded-md prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:before:content-none prose-code:after:content-none prose-pre:rounded-2xl prose-pre:border prose-pre:border-slate-200 prose-pre:bg-slate-950 prose-pre:text-slate-100 dark:prose-invert dark:prose-a:text-shopify-100 dark:prose-code:bg-white/10 dark:prose-pre:border-white/10">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p({ children }) {
                    return (
                      <p
                        dangerouslySetInnerHTML={{
                          __html: highlightCitations(
                            typeof children === "string"
                              ? children
                              : Array.isArray(children)
                              ? children
                                  .map((c) => (typeof c === "string" ? c : ""))
                                  .join("")
                              : ""
                          ),
                        }}
                      />
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        <div className={`mt-2 flex items-center gap-2 text-xs text-slate-400 ${isUser ? "pr-2" : "pl-2"}`}>
          <span>{message.timestamp}</span>
          {!isUser ? (
            <>
              <span>•</span>
              <button
                type="button"
                onClick={copyAnswer}
                className="inline-flex items-center gap-1 rounded-lg px-1.5 py-1 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-white/10 dark:hover:text-slate-200"
              >
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </>
          ) : null}
        </div>

        {!isUser && message.sources?.length ? (
          <div className="mt-4 w-full">
            <div className="mb-2 px-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-400 dark:text-slate-500">
              Sources
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {message.sources.map((source) => (
                <SourceCard key={`${message.id}-${source.url}`} source={source} />
              ))}
            </div>
          </div>
        ) : null}

        {!isUser ? (
          <div className="mt-3 px-1 text-xs text-slate-400 dark:text-slate-500">
            {message.latencyMs}ms • {message.model} • {message.chunksUsed} chunks retrieved
          </div>
        ) : null}
      </div>
      </motion.article>
    </>
  );
}
