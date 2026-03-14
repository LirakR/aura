import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface StreamingMessageProps {
  text: string;
}

export function StreamingMessage({ text }: StreamingMessageProps) {
  if (!text) return null;

  return (
    <div className="flex justify-start py-1.5">
      <div className="max-w-[80%] rounded-lg bg-card px-4 py-2.5 ring-1 ring-border/50 text-card-foreground">
        <div className="prose prose-invert prose-sm max-w-none font-mono text-sm leading-relaxed [&_pre]:bg-background/50 [&_pre]:p-3 [&_pre]:rounded-md [&_code]:text-aura-cyan [&_code]:text-xs">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
          <span className="inline-block size-2 animate-pulse rounded-sm bg-aura-cyan ml-0.5" />
        </div>
      </div>
    </div>
  );
}
