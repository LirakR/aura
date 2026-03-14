import { useEffect, useState } from "react";
import { X, FileCode } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface FileViewerProps {
  project: string;
  path: string;
  onClose: () => void;
}

export function FileViewer({ project, path, onClose }: FileViewerProps) {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<{ content: string }>(
        `/kb/project/${encodeURIComponent(project)}/file?path=${encodeURIComponent(path)}`,
      )
      .then((d) => setContent(d.content))
      .catch(() => setContent(null))
      .finally(() => setLoading(false));
  }, [project, path]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border/50 px-3 py-2">
        <div className="flex items-center gap-2 min-w-0">
          <FileCode className="size-3.5 shrink-0 text-aura-cyan" />
          <span className="truncate font-mono text-xs text-muted-foreground">
            {path}
          </span>
        </div>
        <Button size="icon-xs" variant="ghost" onClick={onClose}>
          <X className="size-3.5" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <span className="font-mono text-xs text-muted-foreground aura-pulse">
              Loading...
            </span>
          </div>
        ) : content !== null ? (
          <pre className="p-4 font-mono text-xs leading-relaxed text-foreground/90 whitespace-pre-wrap break-words">
            {content}
          </pre>
        ) : (
          <div className="flex items-center justify-center p-8">
            <span className="font-mono text-xs text-muted-foreground">
              Failed to load file
            </span>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
