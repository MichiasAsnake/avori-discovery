import { FormEvent, useState } from "react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type ChatPanelProps = {
  messages: ChatMessage[];
  isLoading?: boolean;
  onSend: (message: string) => void;
};

export function ChatPanel({ messages, isLoading = false, onSend }: ChatPanelProps) {
  const [draft, setDraft] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextMessage = draft.trim();
    if (!nextMessage) {
      return;
    }
    onSend(nextMessage);
    setDraft("");
  }

  return (
    <section className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6 shadow-[0_20px_50px_rgba(15,23,42,0.06)]">
      <h2 className="text-2xl font-semibold tracking-[-0.03em] text-slate-900">Strategy chat</h2>
      <div className="mt-5 space-y-4">
        {messages.length ? (
          messages.map((message, index) => (
            <div
              className={message.role === "assistant" ? "rounded-2xl bg-[#f4efe6] p-4" : "rounded-2xl bg-slate-900 p-4 text-white"}
              key={`${message.role}-${index}`}
            >
              <p className="text-xs uppercase tracking-[0.25em] opacity-60">{message.role}</p>
              <p className="mt-2 text-sm leading-6">{message.content}</p>
            </div>
          ))
        ) : (
          <p className="text-sm leading-6 text-slate-600">Ask about trends, pricing, comparisons, or the selected product.</p>
        )}
        {isLoading ? (
          <div className="rounded-2xl bg-[#f4efe6] p-4">
            <p className="text-xs uppercase tracking-[0.25em] opacity-60">assistant</p>
            <p className="mt-2 text-sm leading-6">Thinking...</p>
          </div>
        ) : null}
      </div>
      <form className="mt-5 flex gap-3" onSubmit={handleSubmit}>
        <input
          className="flex-1 rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-slate-400"
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask about pricing, risk, or category fit"
          value={draft}
        />
        <button
          className="rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
          type="submit"
        >
          Send
        </button>
      </form>
    </section>
  );
}
