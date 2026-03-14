import { useEffect, useState } from "react";
import { useWS } from "@/contexts/WebSocketContext";

interface FileEvent {
  project_name: string;
  path: string;
  type: "changed" | "deleted";
  timestamp: string;
}

export function useFileEvents(project: string | null) {
  const [recentChanges, setRecentChanges] = useState<FileEvent[]>([]);
  const { subscribe } = useWS();

  useEffect(() => {
    if (!project) {
      setRecentChanges([]);
      return;
    }

    const unsubs = [
      subscribe("project.file_changed", (msg) => {
        const p = msg.payload as { project_name: string; path: string };
        if (p.project_name === project) {
          setRecentChanges((prev) => [
            { ...p, type: "changed", timestamp: msg.timestamp },
            ...prev.slice(0, 49),
          ]);
        }
      }),
      subscribe("project.file_deleted", (msg) => {
        const p = msg.payload as { project_name: string; path: string };
        if (p.project_name === project) {
          setRecentChanges((prev) => [
            { ...p, type: "deleted", timestamp: msg.timestamp },
            ...prev.slice(0, 49),
          ]);
        }
      }),
    ];

    return () => {
      for (const unsub of unsubs) unsub();
    };
  }, [project, subscribe]);

  return { recentChanges };
}
