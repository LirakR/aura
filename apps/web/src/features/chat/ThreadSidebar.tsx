import { Plus, MessageSquare, Trash2 } from "lucide-react";
import { useNavigate, useParams } from "react-router";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { ProjectSelector } from "./ProjectSelector";
import { useChat } from "@/contexts/ChatContext";
import { useThreads } from "@/hooks/use-chat";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { ChatThread } from "@/types/chat";

export function ThreadSidebar() {
  const { activeProject, setActiveProject, setActiveThreadId } = useChat();
  const { threads, refresh } = useThreads(activeProject);
  const { threadId } = useParams();
  const navigate = useNavigate();

  const handleNewThread = async () => {
    if (!activeProject) return;
    try {
      const thread = await api.post<ChatThread>("/chat/threads", {
        project: activeProject,
      });
      // Extract the ID portion after the colon
      const id = thread.id.includes(":") ? thread.id.split(":")[1] : thread.id;
      setActiveThreadId(id);
      navigate(`/chat/${id}`);
      refresh();
    } catch (err) {
      console.error("Failed to create thread", err);
    }
  };

  const handleDelete = async (e: React.MouseEvent, tid: string) => {
    e.stopPropagation();
    try {
      await api.delete(`/chat/threads/${tid}`);
      if (threadId === tid) {
        navigate("/chat");
        setActiveThreadId(null);
      }
      refresh();
    } catch (err) {
      console.error("Failed to delete thread", err);
    }
  };

  const selectThread = (t: ChatThread) => {
    const id = t.id.includes(":") ? t.id.split(":")[1] : t.id;
    setActiveThreadId(id);
    navigate(`/chat/${id}`);
  };

  return (
    <div className="flex h-full w-64 shrink-0 flex-col border-r border-border/50">
      <div className="p-3">
        <ProjectSelector
          value={activeProject}
          onChange={(p) => {
            setActiveProject(p);
            setActiveThreadId(null);
            navigate("/chat");
          }}
        />
      </div>

      <Separator />

      <div className="p-3">
        <Button
          size="sm"
          variant="outline"
          className="w-full gap-2 font-mono text-xs"
          onClick={handleNewThread}
          disabled={!activeProject}
        >
          <Plus className="size-3.5" />
          New Thread
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-0.5 px-2 pb-2">
          {threads.map((t) => {
            const tid = t.id.includes(":") ? t.id.split(":")[1] : t.id;
            const isActive = tid === threadId;
            return (
              <button
                key={t.id}
                onClick={() => selectThread(t)}
                className={cn(
                  "group flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left font-mono text-xs transition-colors",
                  isActive
                    ? "bg-secondary text-foreground"
                    : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground",
                )}
              >
                <MessageSquare className="size-3.5 shrink-0" />
                <span className="flex-1 truncate">{t.title}</span>
                <button
                  onClick={(e) => handleDelete(e, tid)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 className="size-3 text-muted-foreground hover:text-aura-red" />
                </button>
              </button>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
