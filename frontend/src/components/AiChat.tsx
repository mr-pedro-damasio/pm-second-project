"use client";

import { useRef, useEffect, useState } from "react";
import type { BoardData } from "@/lib/kanban";
import { aiChat, toBoardForChat } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

type Props = {
  board: BoardData;
  onBoardUpdate: () => Promise<void>;
};

export const AiChat = ({ board, onBoardUpdate }: Props) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await aiChat(
        [...messages, userMsg].map((m) => ({ role: m.role, content: m.content })),
        toBoardForChat(board)
      );
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.message },
      ]);
      if (res.board_updated) {
        await onBoardUpdate();
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setSending(false);
    }
  };

  if (collapsed) {
    return (
      <aside className="sticky top-6 flex w-12 shrink-0 flex-col items-center gap-3 rounded-3xl border border-[var(--stroke)] bg-white/80 py-4 shadow-[var(--shadow)] backdrop-blur">
        <button
          onClick={() => setCollapsed(false)}
          className="rounded-xl p-2 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
          aria-label="Expand AI chat"
          title="Open AI chat"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </button>
        {messages.length > 0 && (
          <span className="h-2 w-2 rounded-full bg-[var(--purple-secondary)]" />
        )}
      </aside>
    );
  }

  return (
    <aside className="sticky top-6 flex max-h-[calc(100vh-3rem)] w-80 shrink-0 flex-col overflow-hidden rounded-3xl border border-[var(--stroke)] bg-white/80 shadow-[var(--shadow)] backdrop-blur">
      <div className="flex items-start justify-between border-b border-[var(--stroke)] px-5 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
            AI Assistant
          </p>
          <h2 className="mt-1 font-display text-lg font-semibold text-[var(--navy-dark)]">
            Chat
          </h2>
        </div>
        <button
          onClick={() => setCollapsed(true)}
          className="rounded-xl p-1.5 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
          aria-label="Collapse AI chat"
          title="Collapse"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M9 18l6-6-6-6" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4" style={{ minHeight: 0 }}>
        {messages.length === 0 ? (
          <p className="text-xs leading-5 text-[var(--gray-text)]">
            Ask me to create, move, or edit cards on your board.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`rounded-2xl px-4 py-3 text-sm leading-6 ${
                  msg.role === "user"
                    ? "ml-4 bg-[var(--purple-secondary)] text-white"
                    : "mr-4 bg-[var(--surface)] text-[var(--navy-dark)]"
                }`}
              >
                {msg.content}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="border-t border-[var(--stroke)] px-4 py-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask the AI..."
            disabled={sending}
            className="flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={sending || !input.trim()}
            className="rounded-xl bg-[var(--purple-secondary)] px-4 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {sending ? "..." : "Send"}
          </button>
        </div>
      </div>
    </aside>
  );
};
