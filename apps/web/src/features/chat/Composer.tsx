import { useCallback, useRef, useState } from "react";
import { SendHorizontal, StopCircle } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface ComposerProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  sending?: boolean;
  onInterrupt?: () => void;
}

export function Composer({ onSend, disabled, sending, onInterrupt }: ComposerProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  };

  return (
    <div className="border-t border-border/50 bg-background/80 backdrop-blur-sm p-4">
      <div className="flex items-end gap-2">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={
            disabled
              ? "Select a project to start chatting"
              : "Type a message\u2026"
          }
          disabled={disabled || sending}
          rows={1}
          className="min-h-[40px] max-h-[200px] resize-none font-mono text-sm"
        />
        {onInterrupt ? (
          <Button
            size="icon"
            variant="destructive"
            onClick={onInterrupt}
            className="shrink-0"
          >
            <StopCircle className="size-4" />
          </Button>
        ) : (
          <Button
            size="icon"
            variant="default"
            onClick={handleSend}
            disabled={disabled || sending || !value.trim()}
            className="shrink-0"
          >
            <SendHorizontal className="size-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
