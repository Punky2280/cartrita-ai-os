import React, { useEffect, useMemo, useRef, useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/cjs/styles/prism";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
};

type Props = {
  messages: ChatMessage[];
  fontSize?: "sm" | "md" | "lg";
  autoScroll?: boolean;
  highlightCode?: boolean;
  renderMessage?: (msg: ChatMessage) => React.ReactNode;
};

const rowHeights = { sm: 18, md: 20, lg: 22 };

export default function MessageList({
  messages,
  fontSize = "md",
  autoScroll = true,
  highlightCode = true,
  renderMessage,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [height, setHeight] = useState(600);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onScroll = () => setScrollTop(el.scrollTop);
    const resize = () => setHeight(el.clientHeight);
    el.addEventListener("scroll", onScroll);
    resize();
    window.addEventListener("resize", resize);
    return () => {
      el.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", resize);
    };
  }, []);

  useEffect(() => {
    if (!autoScroll) return;
    const el = containerRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, autoScroll]);

  const estRow = rowHeights[fontSize] * 3; // rough average lines
  const totalHeight = messages.length * estRow;
  const startIndex = Math.max(0, Math.floor(scrollTop / estRow) - 10);
  const visibleCount = Math.ceil(height / estRow) + 20;
  const endIndex = Math.min(messages.length, startIndex + visibleCount);
  const offsetY = startIndex * estRow;

  const slice = useMemo(
    () => messages.slice(startIndex, endIndex),
    [messages, startIndex, endIndex],
  );

  return (
    <div
      ref={containerRef}
      className={`relative overflow-y-auto w-full h-full ${fontSize === "sm" ? "text-sm" : fontSize === "lg" ? "text-lg" : "text-base"}`}
      role="log"
      aria-live="polite"
    >
      <div style={{ height: totalHeight }} />
      <div
        className="absolute left-0 right-0"
        style={{ transform: `translateY(${offsetY}px)` }}
      >
        {slice.map((m) => (
          <div key={m.id}>
            {renderMessage ? (
              <>{renderMessage(m)}</>
            ) : (
              <MessageRow msg={m} highlightCode={highlightCode} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function MessageRow({
  msg,
  highlightCode,
}: {
  msg: ChatMessage;
  highlightCode: boolean;
}) {
  const isUser = msg.role === "user";
  const isSystem = msg.role === "system";

  return (
    <div className="px-3 py-2">
      <div className={`max-w-3xl ${isUser ? "ml-auto text-right" : ""}`}>
        <div
          className={`mb-1 text-xs uppercase tracking-wide ${isSystem ? "text-amber-400" : isUser ? "text-sky-400" : "text-emerald-400"}`}
        >
          {msg.role}
        </div>
        <MarkdownBlock content={msg.content} highlightCode={highlightCode} />
      </div>
    </div>
  );
}

function MarkdownBlock({
  content,
  highlightCode,
}: {
  content: string;
  highlightCode: boolean;
}) {
  // Very light markdown for code fences and inline code; avoids heavy libs.
  // Supports ```lang\ncode\n``` and inline `code`.
  const parts = useMemo(() => splitFences(content), [content]);
  return (
    <div className="prose prose-invert max-w-none">
      {parts.map((p, i) =>
        p.type === "code" ? (
          <CodeFence
            key={i}
            lang={p.lang}
            code={p.text}
            highlightCode={highlightCode}
          />
        ) : (
          <p key={i}>{renderInlineCode(p.text)}</p>
        ),
      )}
    </div>
  );
}

function CodeFence({
  lang,
  code,
  highlightCode,
}: {
  lang: string | null;
  code: string;
  highlightCode: boolean;
}) {
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
    } catch {
      // ignore copy errors silently
    }
  };
  return (
    <div className="relative group">
      <button
        onClick={onCopy}
        className="absolute right-2 top-2 text-xs rounded bg-gray-800/80 border border-gray-700 px-2 py-0.5 opacity-0 group-hover:opacity-100"
        aria-label="Copy code"
      >
        Copy
      </button>
      {highlightCode ? (
        <SyntaxHighlighter
          language={(lang || "text") as any}
          style={vscDarkPlus}
          customStyle={{ margin: 0, background: "transparent" }}
        >
          {code}
        </SyntaxHighlighter>
      ) : (
        <pre className="overflow-x-auto bg-black/60 border border-gray-800 rounded p-3">
          <code className={`language-${lang || "text"}`}>{code}</code>
        </pre>
      )}
    </div>
  );
}

function splitFences(
  text: string,
): Array<{ type: "text" | "code"; text: string; lang: string | null }> {
  const out: Array<{
    type: "text" | "code";
    text: string;
    lang: string | null;
  }> = [];
  const fence = /```(\w+)?\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = fence.exec(text)) !== null) {
    if (m.index > lastIndex)
      out.push({
        type: "text",
        text: text.slice(lastIndex, m.index),
        lang: null,
      });
    out.push({
      type: "code",
      text: m[2].trimEnd(),
      lang: (m[1] || null) as any,
    });
    lastIndex = m.index + m[0].length;
  }
  if (lastIndex < text.length)
    out.push({ type: "text", text: text.slice(lastIndex), lang: null });
  return out;
}

function renderInlineCode(text: string) {
  const segments = text.split(/(`[^`]+`)/g);
  return segments.map((seg, i) => {
    if (seg.startsWith("`") && seg.endsWith("`")) {
      return (
        <code
          key={i}
          className="bg-gray-800 px-1 rounded border border-gray-700"
        >
          {seg.slice(1, -1)}
        </code>
      );
    }
    return <React.Fragment key={i}>{seg}</React.Fragment>;
  });
}
