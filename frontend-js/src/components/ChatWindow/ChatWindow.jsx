import { useEffect, useRef } from "react";
import { MessageBubble } from "../MessageBubble/MessageBubble";
import { LoadingState } from "../LoadingState/LoadingState";
import { SearchBar } from "../SearchBar/SearchBar";
import { ErrorState } from "../ErrorState/ErrorState";
import { EmptyState } from "../EmptyState/EmptyState";

export function ChatWindow({ messages, isLoading, error, onAsk, onDismissError }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading, error]);

  return (
    <main className="flex min-h-screen flex-1 flex-col bg-slate-50 dark:bg-ink-950">
      <div className="flex-1 overflow-y-auto px-4 pb-36 pt-20 lg:px-8 lg:pt-8">
        <div className="mx-auto max-w-5xl space-y-7">
          {messages.length === 0 && !isLoading ? <EmptyState /> : null}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading ? <LoadingState /> : null}
          {error ? <ErrorState error={error} onDismiss={onDismissError} /> : null}
          <div ref={endRef} />
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 border-t border-slate-200/80 bg-slate-50/85 px-4 py-4 backdrop-blur-xl lg:left-80 lg:px-8 dark:border-white/10 dark:bg-ink-950/85">
        <div className="mx-auto max-w-5xl">
          <SearchBar onSubmit={onAsk} isLoading={isLoading} />
          <div className="mt-2 text-center text-xs text-slate-400 dark:text-slate-500">
            Answers are generated from retrieved Shopify documentation. Verify critical store settings before applying changes.
          </div>
        </div>
      </div>
    </main>
  );
}
