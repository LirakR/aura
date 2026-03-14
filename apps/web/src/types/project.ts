export interface Project {
  id: string;
  name: string;
  engine: string;
  engine_version: string | null;
  path: string | null;
  last_scan: string | null;
}

export interface ProjectFile {
  path: string;
  language: string | null;
  updated_at: string | null;
}

export interface ProjectDetail extends Project {
  files: ProjectFile[];
}
