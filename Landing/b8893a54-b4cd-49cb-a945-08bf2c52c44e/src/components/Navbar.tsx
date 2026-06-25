import { Volume2, VolumeX, Atom } from "lucide-react";
import { personal, tabs } from "@/data/portfolioData";
import { audioManager, useAudioManager } from "@/lib/audioManager";

interface NavbarProps {
  activeTab: string;
  onTabChange: (id: string) => void;
}

export function Navbar({ activeTab, onTabChange }: NavbarProps) {
  const { muted } = useAudioManager();

  function handleMuteToggle() {
    audioManager.toggleMute();
  }

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/50 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo / Name */}
        <div className="flex items-center gap-2">
          <Atom
            className="h-5 w-5 text-accent"
            aria-hidden="true"
            strokeWidth={1.5}
          />
          <span className="font-heading text-sm font-semibold tracking-tight text-foreground">
            {personal.name}
          </span>
        </div>

        {/* Tab navigation */}
        <nav aria-label="Portfolio sections">
          <ul className="flex items-center gap-1" role="tablist">
            {tabs.map((tab) => (
              <li key={tab.id} role="presentation">
                <button
                  role="tab"
                  aria-selected={activeTab === tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={[
                    "cursor-pointer rounded-md px-4 py-1.5 text-sm font-medium transition-colors duration-200",
                    activeTab === tab.id
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                  ].join(" ")}
                >
                  {tab.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Global mute toggle */}
        <button
          onClick={handleMuteToggle}
          aria-label={muted ? "Unmute audio" : "Mute audio"}
          title={muted ? "Unmute" : "Mute"}
          className="cursor-pointer rounded-full border border-border p-2 text-muted-foreground transition-colors hover:border-accent hover:text-accent"
        >
          {muted ? (
            <VolumeX className="h-4 w-4" aria-hidden="true" />
          ) : (
            <Volume2 className="h-4 w-4" aria-hidden="true" />
          )}
        </button>
      </div>
    </header>
  );
}
