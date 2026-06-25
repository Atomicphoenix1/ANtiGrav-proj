import { Mail, Phone, MapPin, Github, Volume2, VolumeX } from "lucide-react";
import { personal } from "@/data/portfolioData";
import { audioManager, useAudioManager } from "@/lib/audioManager";
import { SplineViewer } from "@/components/SplineViewer";
import type { SocialLink } from "@/data/portfolioData";

const ICON_MAP: Record<SocialLink["icon"], typeof Mail> = {
  email: Mail,
  phone: Phone,
  location: MapPin,
  github: Github,
};

export function HeroSection() {
  const { muted, playingId } = useAudioManager();
  const isPlaying = playingId === "welcome";

  function handleWelcomeToggle() {
    audioManager.toggle("welcome", personal.welcomeAudioSrc);
  }

  return (
    <section
      aria-label="Introduction"
      className="mx-auto grid max-w-7xl grid-cols-1 items-center gap-10 px-6 py-16 lg:grid-cols-2 lg:py-24"
    >
      {/* ── Left: Bio ────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-6">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-accent">
            Portfolio
          </p>
          <h1 className="font-heading text-4xl font-bold leading-tight tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            {personal.name}
          </h1>
          <p className="mt-3 text-xl font-medium text-muted-foreground">
            {personal.title}
          </p>
        </div>

        <p className="max-w-prose text-base leading-relaxed text-foreground/80">
          {personal.tagline}
        </p>

        {/* Social links */}
        <ul className="flex flex-wrap gap-3">
          {personal.socials.map((s) => {
            const Icon = ICON_MAP[s.icon];
            return (
              <li key={s.label}>
                <a
                  href={s.url}
                  className="group flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-accent hover:text-accent"
                  target={s.url.startsWith("http") ? "_blank" : undefined}
                  rel={s.url.startsWith("http") ? "noreferrer" : undefined}
                >
                  <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>{s.label}</span>
                </a>
              </li>
            );
          })}
        </ul>

        {/* Welcome audio button */}
        <button
          onClick={handleWelcomeToggle}
          aria-label={isPlaying ? "Pause welcome narration" : "Play welcome narration"}
          className="group flex w-fit items-center gap-2 rounded-full bg-accent px-5 py-2.5 text-sm font-semibold text-accent-foreground transition-opacity hover:opacity-90 active:scale-[0.97]"
        >
          {isPlaying && !muted ? (
            <>
              <VolumeX className="h-4 w-4" aria-hidden="true" />
              Pause narration
            </>
          ) : (
            <>
              <Volume2 className="h-4 w-4" aria-hidden="true" />
              Play welcome narration
            </>
          )}
        </button>
      </div>

      {/* ── Right: Spline 3D ─────────────────────────────────────────── */}
      <div className="relative h-[380px] w-full lg:h-[520px]">
        {/* Card wrapper with border */}
        <div className="absolute inset-0 rounded-2xl border border-border/40 bg-card/20 shadow-xl">
          <SplineViewer />
        </div>
        {/* Subtle accent glow */}
        <div
          className="pointer-events-none absolute -inset-1 rounded-2xl opacity-20 blur-2xl"
          style={{ background: "var(--accent)" }}
          aria-hidden="true"
        />
      </div>
    </section>
  );
}
