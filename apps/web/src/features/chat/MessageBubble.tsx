import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import { FileChangeNotice } from "./FileChangeNotice";
import type { ChatMessage } from "@/types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const { role, content, metadata } = message;

  if (role === "system") {
    // File change notifications get a special display
    const meta = metadata as { type?: string } | null;
    if (meta?.type === "file_change" || meta?.type === "file_delete") {
      return <FileChangeNotice message={message} />;
    }

    return (
      <div className="flex justify-center py-2">
        <span className="rounded-md bg-muted/50 px-3 py-1.5 font-mono text-[11px] text-muted-foreground">
          {content}
        </span>
      </div>
    );
  }

  const isUser = role === "user";

  return (
    <div
      className={cn("flex py-1.5", isUser ? "justify-end" : "justify-start")}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2.5",
          isUser
            ? "bg-aura-cyan/10 text-foreground"
            : "bg-card text-card-foreground ring-1 ring-border/50",
        )}
      >
        <div className="prose prose-invert prose-sm max-w-none font-mono text-sm leading-relaxed [&_pre]:bg-background/50 [&_pre]:p-3 [&_pre]:rounded-md [&_code]:text-aura-cyan [&_code]:text-xs">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
        <div className="mt-1.5 flex justify-end">
          <time className="font-mono text-[10px] text-muted-foreground/50">
            {new Date(message.created_at).toLocaleTimeString()}
          </time>
        </div>
      </div>
    </div>
  );
}
