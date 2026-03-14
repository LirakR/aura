import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";

interface ChatContextValue {
  activeProject: string | null;
  setActiveProject: (project: string | null) => void;
  activeThreadId: string | null;
  setActiveThreadId: (id: string | null) => void;
}

const Ctx = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [activeProject, setActiveProject] = useState<string | null>(null);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);

  return (
    <Ctx.Provider
      value={{
        activeProject,
        setActiveProject,
        activeThreadId,
        setActiveThreadId,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useChat(): ChatContextValue {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useChat must be used within a ChatProvider");
  return ctx;
}
