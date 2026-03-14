import { FileEdit, FileX } from "lucide-react";
import type { ChatMessage } from "@/types/chat";

interface FileChangeNoticeProps {
  message: ChatMessage;
}

export function FileChangeNotice({ message }: FileChangeNoticeProps) {
  const meta = message.metadata as { type?: string; path?: string } | null;
  const isDelete = meta?.type === "file_delete";
  const path = meta?.path || message.content;

  return (
    <div className="flex justify-center py-1">
      <div className="flex items-center gap-2 rounded-md bg-muted/30 px-3 py-1.5">
        {isDelete ? (
          <FileX className="size-3 text-aura-red" />
        ) : (
          <FileEdit className="size-3 text-aura-amber" />
        )}
        <span className="font-mono text-[11px] text-muted-foreground">
          {path}
        </span>
      </div>
    </div>
  );
}
