import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router";
import { PanelRightClose, PanelRightOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ThreadSidebar } from "./ThreadSidebar";
import { MessageList } from "./MessageList";
import { Composer } from "./Composer";
import { AgentStatus } from "./AgentStatus";
import { FileBrowser } from "@/features/projects/FileBrowser";
import { FileViewer } from "@/features/projects/FileViewer";
import { useChat } from "@/contexts/ChatContext";
import { useMessages, useSendMessage } from "@/hooks/use-chat";
import { useAgent } from "@/hooks/use-agent";

export function ChatPage() {
  const { threadId } = useParams();
  const { activeProject, setActiveThreadId } = useChat();
  const { messages, loading, hasMore, loadMore } = useMessages(threadId ?? null);
  const { sendMessage, sending } = useSendMessage();
  const {
    turnState,
    streamingText,
    items: turnItems,
    approvalRequest,
    sendToAgent,
    interrupt,
    respondToApproval,
  } = useAgent(threadId ?? null);
  const [filePanelOpen, setFilePanelOpen] = useState(false);
  const [viewingFile, setViewingFile] = useState<string | null>(null);

  useEffect(() => {
    setActiveThreadId(threadId ?? null);
  }, [threadId, setActiveThreadId]);

  const handleSend = useCallback(
    (content: string) => {
      if (!threadId) return;
      // Send through WS so agent gets triggered
      sendToAgent(threadId, content);
    },
    [threadId, sendToAgent],
  );

  const handleInterrupt = useCallback(() => {
    if (threadId) interrupt(threadId);
  }, [threadId, interrupt]);

  const handleApproval = useCallback(
    (decision: "approve" | "deny") => {
      if (threadId && approvalRequest) {
        respondToApproval(threadId, approvalRequest.request_id, decision);
      }
    },
    [threadId, approvalRequest, respondToApproval],
  );

  const handleFileSelect = useCallback((path: string) => {
    setViewingFile(path);
  }, []);

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Thread sidebar */}
      <ThreadSidebar />

      {/* Main chat area */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Thread header */}
        {threadId && (
          <div className="flex items-center justify-between border-b border-border/50 px-4 py-2">
            <span className="font-mono text-xs text-muted-foreground">
              {activeProject && (
                <span className="text-aura-cyan">{activeProject}</span>
              )}
            </span>
            <Button
              size="icon-xs"
              variant="ghost"
              onClick={() => setFilePanelOpen(!filePanelOpen)}
              className="text-muted-foreground"
            >
              {filePanelOpen ? (
                <PanelRightClose className="size-4" />
              ) : (
                <PanelRightOpen className="size-4" />
              )}
            </Button>
          </div>
        )}

        {/* Messages */}
        {threadId ? (
          <>
            <MessageList
              messages={messages}
              hasMore={hasMore}
              onLoadMore={loadMore}
              loading={loading}
              streamingText={streamingText}
              turnItems={turnItems}
              approvalRequest={approvalRequest}
              onApprovalRespond={handleApproval}
            />
            <AgentStatus state={turnState} />
            <Composer
              onSend={handleSend}
              disabled={!threadId}
              sending={sending || turnState !== "idle"}
              onInterrupt={turnState !== "idle" ? handleInterrupt : undefined}
            />
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center">
            <div className="text-center space-y-2">
              <p className="font-mono text-sm text-muted-foreground">
                {activeProject
                  ? "Select or create a thread to start chatting"
                  : "Select a project to get started"}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* File panel */}
      {filePanelOpen && threadId && (
        <>
          <Separator orientation="vertical" />
          <div className="flex w-72 shrink-0 flex-col">
            {viewingFile && activeProject ? (
              <FileViewer
                project={activeProject}
                path={viewingFile}
                onClose={() => setViewingFile(null)}
              />
            ) : (
              <>
                <div className="border-b border-border/50 px-3 py-2">
                  <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                    Project Files
                  </span>
                </div>
                <FileBrowser
                  project={activeProject}
                  onFileSelect={handleFileSelect}
                />
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
