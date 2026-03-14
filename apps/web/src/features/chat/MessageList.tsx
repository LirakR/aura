import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "./MessageBubble";
import { StreamingMessage } from "./StreamingMessage";
import { ApprovalCard } from "./ApprovalCard";
import { TurnItemCard } from "./TurnItemCard";
import type { ChatMessage } from "@/types/chat";
import type { ApprovalRequest, TurnItem } from "@/types/agent";

interface MessageListProps {
  messages: ChatMessage[];
  hasMore: boolean;
  onLoadMore: () => void;
  loading: boolean;
  streamingText?: string;
  turnItems?: TurnItem[];
  approvalRequest?: ApprovalRequest | null;
  onApprovalRespond?: (decision: "approve" | "deny") => void;
}

export function MessageList({
  messages,
  hasMore,
  onLoadMore,
  loading,
  streamingText,
  turnItems,
  approvalRequest,
  onApprovalRespond,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const prevCountRef = useRef(0);

  // Auto-scroll on new content
  useEffect(() => {
    const hasNewContent =
      messages.length > prevCountRef.current ||
      (streamingText && streamingText.length > 0) ||
      (turnItems && turnItems.length > 0);
    if (hasNewContent) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
    prevCountRef.current = messages.length;
  }, [messages.length, streamingText, turnItems?.length]);

  if (messages.length === 0 && !loading && !streamingText) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="font-mono text-sm text-muted-foreground/50">
          No messages yet. Start the conversation.
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div className="flex flex-col gap-1 px-4 py-4">
        {hasMore && (
          <button
            onClick={onLoadMore}
            className="mx-auto mb-2 font-mono text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Load earlier messages
          </button>
        )}

        {/* Persisted messages */}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Live turn items (tool calls, file changes) */}
        {turnItems?.map((item) => (
          <TurnItemCard key={item.id} item={item} />
        ))}

        {/* Currently streaming agent message */}
        {streamingText && <StreamingMessage text={streamingText} />}

        {/* Approval request */}
        {approvalRequest && onApprovalRespond && (
          <ApprovalCard
            request={approvalRequest}
            onRespond={onApprovalRespond}
          />
        )}

        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
