import { useState } from "react";
import { Terminal, FileEdit, ChevronDown, ChevronRight, Loader2, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TurnItem } from "@/types/agent";

interface TurnItemCardProps {
  item: TurnItem;
}

export function TurnItemCard({ item }: TurnItemCardProps) {
  const [expanded, setExpanded] = useState(false);
  const isRunning = item.status === "running";

  if (item.type === "message") return null; // messages are rendered separately

  const Icon = item.type === "command" ? Terminal : FileEdit;
  const label =
    item.type === "command"
      ? item.command || "Running command..."
      : `File change${item.files?.length ? `: ${item.files.join(", ")}` : ""}`;

  return (
    <div className="flex justify-start py-1">
      <div className="max-w-[80%] rounded-md border border-border/50 bg-card/50">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center gap-2 px-3 py-2 text-left"
        >
          {isRunning ? (
            <Loader2 className="size-3.5 shrink-0 animate-spin text-aura-cyan" />
          ) : (
            <Check className="size-3.5 shrink-0 text-aura-green" />
          )}
          <Icon className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="flex-1 truncate font-mono text-xs text-muted-foreground">
            {label}
          </span>
          {item.output && (
            expanded ? (
              <ChevronDown className="size-3 shrink-0 text-muted-foreground" />
            ) : (
              <ChevronRight className="size-3 shrink-0 text-muted-foreground" />
            )
          )}
        </button>
        {expanded && item.output && (
          <pre className="max-h-40 overflow-auto border-t border-border/30 px-3 py-2 font-mono text-[11px] text-muted-foreground/80 whitespace-pre-wrap">
            {item.output}
          </pre>
        )}
      </div>
    </div>
  );
}
