import { ArrowUp, Loader2 } from "lucide-react";
import { useState } from "react";

export function SearchBar({
  onSubmit,
  isLoading = false,
  autoFocus = false,
  placeholder = "Ask about shipping, payments, products, orders..."
}) {
  const [value, setValue] = useState("");

  function submitValue() {
    const question = value.trim();
    if (!question) return;
    onSubmit(question);
    setValue("");
  }

  function handleSubmit(event) {
    event.preventDefault();
    submitValue();
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submitValue();
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-3 rounded-2xl border border-slate-200 bg-white p-2 shadow-soft transition focus-within:border-shopify-500 focus-within:ring-4 focus-within:ring-shopify-500/10 dark:border-white/10 dark:bg-ink-900 dark:focus-within:border-shopify-500/80"
    >
      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
        autoFocus={autoFocus}
        placeholder={placeholder}
        className="max-h-36 min-h-12 flex-1 resize-none bg-transparent px-3 py-3 text-[15px] leading-6 text-slate-950 outline-none placeholder:text-slate-400 dark:text-white dark:placeholder:text-slate-500"
      />
      <button
        type="submit"
        disabled={isLoading || !value.trim()}
        className="mb-1 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-shopify-500 text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-shopify-600 disabled:translate-y-0 disabled:bg-slate-300 disabled:shadow-none dark:disabled:bg-white/10"
        aria-label="Ask question"
      >
        {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
      </button>
    </form>
  );
}
