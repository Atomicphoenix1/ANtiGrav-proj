import { useState } from "react";
import { Play, Pause, Code2 } from "lucide-react";
import { audioManager, useAudioManager } from "@/lib/audioManager";
import { CodePreviewWindow } from "@/components/CodePreviewWindow";
import type { Project } from "@/data/portfolioData";

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const { playingId } = useAudioManager();
  const [showCode, setShowCode] = useState(false);

  const isPlaying = playingId === project.id;

  function handleAudioToggle() {
    if (!project.audioSrc) return;
    audioManager.toggle(project.id, project.audioSrc);
  }

  return (
    <>
      <article className="group flex flex-col gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-heading text-base font-semibold leading-snug text-card-foreground">
            {project.title}
          </h3>

          {/* Audio story button */}
          {project.audioSrc && (
            <button
              onClick={handleAudioToggle}
              aria-label={isPlaying ? `Pause "${project.title}" narration` : `Play "${project.title}" story`}
              title={isPlaying ? "Pause story" : "Play story"}
              className="flex shrink-0 cursor-pointer items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-accent hover:text-accent"
            >
              {isPlaying ? (
                <>
                  <Pause className="h-3 w-3" aria-hidden="true" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="h-3 w-3" aria-hidden="true" />
                  Story
                </>
              )}
            </button>
          )}
        </div>

        {/* Description */}
        <p className="text-sm leading-relaxed text-muted-foreground">
          {project.description}
        </p>

        {/* Tech stack badges */}
        <ul className="flex flex-wrap gap-2" aria-label="Technologies used">
          {project.techStack.map((tech) => (
            <li
              key={tech}
              className="rounded-md bg-secondary px-2.5 py-1 text-xs font-medium text-secondary-foreground"
            >
              {tech}
            </li>
          ))}
        </ul>

        {/* Footer actions */}
        {project.codePreview && (
          <div className="mt-auto pt-2">
            <button
              onClick={() => setShowCode(true)}
              className="flex cursor-pointer items-center gap-2 text-xs font-medium text-accent transition-opacity hover:opacity-80"
            >
              <Code2 className="h-3.5 w-3.5" aria-hidden="true" />
              View code preview
            </button>
          </div>
        )}
      </article>

      {/* Code preview modal — rendered outside card to avoid z-index issues */}
      {showCode && project.codePreview && (
        <CodePreviewWindow
          projectId={project.id}
          config={project.codePreview}
          onClose={() => setShowCode(false)}
        />
      )}
    </>
  );
}
