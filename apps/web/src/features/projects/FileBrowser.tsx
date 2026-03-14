import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ChevronRight,
  ChevronDown,
  File,
  Folder,
  FolderOpen,
} from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useFileEvents } from "@/hooks/use-file-events";
import type { ProjectDetail, ProjectFile } from "@/types/project";

interface FileBrowserProps {
  project: string | null;
  onFileSelect?: (path: string) => void;
}

interface TreeNode {
  name: string;
  path: string;
  isDir: boolean;
  children: TreeNode[];
  file?: ProjectFile;
}

function buildTree(files: ProjectFile[]): TreeNode[] {
  const root: TreeNode[] = [];

  for (const f of files) {
    const parts = f.path.split("/");
    let nodes = root;

    for (let i = 0; i < parts.length; i++) {
      const name = parts[i];
      const isLast = i === parts.length - 1;
      const path = parts.slice(0, i + 1).join("/");

      let existing = nodes.find((n) => n.name === name);
      if (!existing) {
        existing = {
          name,
          path,
          isDir: !isLast,
          children: [],
          file: isLast ? f : undefined,
        };
        nodes.push(existing);
      }
      nodes = existing.children;
    }
  }

  const sortNodes = (nodes: TreeNode[]) => {
    nodes.sort((a, b) => {
      if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    for (const n of nodes) sortNodes(n.children);
  };
  sortNodes(root);
  return root;
}

function TreeItem({
  node,
  depth,
  onSelect,
  selectedPath,
  recentPaths,
}: {
  node: TreeNode;
  depth: number;
  onSelect: (path: string) => void;
  selectedPath: string | null;
  recentPaths: Set<string>;
}) {
  const [open, setOpen] = useState(depth < 1);
  const isSelected = node.path === selectedPath;
  const isRecent = recentPaths.has(node.path);

  if (node.isDir) {
    return (
      <>
        <button
          onClick={() => setOpen(!open)}
          className="flex w-full items-center gap-1.5 rounded-sm px-1.5 py-1 font-mono text-xs text-muted-foreground hover:bg-secondary/50 hover:text-foreground transition-colors"
          style={{ paddingLeft: depth * 12 + 6 }}
        >
          {open ? (
            <ChevronDown className="size-3 shrink-0" />
          ) : (
            <ChevronRight className="size-3 shrink-0" />
          )}
          {open ? (
            <FolderOpen className="size-3.5 shrink-0 text-aura-amber" />
          ) : (
            <Folder className="size-3.5 shrink-0 text-aura-amber" />
          )}
          <span className="truncate">{node.name}</span>
        </button>
        {open &&
          node.children.map((child) => (
            <TreeItem
              key={child.path}
              node={child}
              depth={depth + 1}
              onSelect={onSelect}
              selectedPath={selectedPath}
              recentPaths={recentPaths}
            />
          ))}
      </>
    );
  }

  return (
    <button
      onClick={() => onSelect(node.path)}
      className={cn(
        "flex w-full items-center gap-1.5 rounded-sm px-1.5 py-1 font-mono text-xs transition-colors",
        isSelected
          ? "bg-aura-cyan/10 text-foreground"
          : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground",
      )}
      style={{ paddingLeft: depth * 12 + 6 }}
    >
      <span className="size-3 shrink-0" />
      <File className="size-3.5 shrink-0 text-muted-foreground" />
      <span className="truncate">{node.name}</span>
      {isRecent && (
        <span className="ml-auto size-1.5 shrink-0 rounded-full bg-aura-amber aura-pulse" />
      )}
    </button>
  );
}

export function FileBrowser({ project, onFileSelect }: FileBrowserProps) {
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const { recentChanges } = useFileEvents(project);

  useEffect(() => {
    if (!project) {
      setFiles([]);
      return;
    }
    api
      .get<ProjectDetail>(`/projects/${encodeURIComponent(project)}`)
      .then((d) => setFiles(d.files))
      .catch((err) => console.error("Failed to load project files", err));
  }, [project]);

  const tree = useMemo(() => buildTree(files), [files]);

  const recentPaths = useMemo(
    () => new Set(recentChanges.map((c) => c.path)),
    [recentChanges],
  );

  const handleSelect = useCallback(
    (path: string) => {
      setSelectedPath(path);
      onFileSelect?.(path);
    },
    [onFileSelect],
  );

  if (!project) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <p className="font-mono text-xs text-muted-foreground/50">
          Select a project
        </p>
      </div>
    );
  }

  if (files.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <p className="font-mono text-xs text-muted-foreground/50">
          No files indexed
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="p-2">
        {tree.map((node) => (
          <TreeItem
            key={node.path}
            node={node}
            depth={0}
            onSelect={handleSelect}
            selectedPath={selectedPath}
            recentPaths={recentPaths}
          />
        ))}
      </div>
    </ScrollArea>
  );
}
