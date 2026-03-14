import { useEffect, useState } from "react";
import { FolderOpen, ChevronDown } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Project } from "@/types/project";

interface ProjectSelectorProps {
  value: string | null;
  onChange: (project: string) => void;
}

export function ProjectSelector({ value, onChange }: ProjectSelectorProps) {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    api
      .get<Project[]>("/projects")
      .then(setProjects)
      .catch((err) => console.error("Failed to load projects", err));
  }, []);

  const selected = projects.find((p) => p.name === value);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="w-full justify-between font-mono text-xs"
        >
          <span className="flex items-center gap-2 truncate">
            <FolderOpen className="size-3.5 shrink-0 text-aura-cyan" />
            {selected ? selected.name : "Select project"}
          </span>
          <ChevronDown className="size-3 shrink-0 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {projects.length === 0 && (
          <DropdownMenuItem disabled className="font-mono text-xs">
            No projects found
          </DropdownMenuItem>
        )}
        {projects.map((p) => (
          <DropdownMenuItem
            key={p.id}
            className="font-mono text-xs"
            onSelect={() => onChange(p.name)}
          >
            <FolderOpen className="mr-2 size-3.5 text-aura-cyan" />
            {p.name}
            <span className="ml-auto text-[10px] text-muted-foreground">
              {p.engine}
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
