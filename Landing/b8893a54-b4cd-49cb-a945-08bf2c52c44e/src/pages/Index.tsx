import { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { HeroSection } from "@/components/HeroSection";
import { ProjectsSection } from "@/components/sections/ProjectsSection";
import { SkillsSection } from "@/components/sections/SkillsSection";
import { EducationSection } from "@/components/sections/EducationSection";
import { ExperienceSection } from "@/components/sections/ExperienceSection";
import { tabs } from "@/data/portfolioData";

const SECTION_MAP = {
  projects: ProjectsSection,
  skills: SkillsSection,
  education: EducationSection,
  experience: ExperienceSection,
} as const;

export default function Index() {
  const [activeTab, setActiveTab] = useState(tabs[0].id);

  const currentTab = tabs.find((t) => t.id === activeTab) ?? tabs[0];

  return (
    <div className="min-h-dvh bg-background text-foreground">
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

      <main>
        <HeroSection />

        {/* Tab content */}
        <div className="border-t border-border/40">
          <div className="mx-auto max-w-7xl px-6 py-12 sm:py-16">
            <div
              role="tabpanel"
              aria-label={currentTab.label}
              className="flex flex-col gap-16"
            >
              {currentTab.sectionIds.map((sectionId) => {
                const Section = SECTION_MAP[sectionId];
                return <Section key={sectionId} />;
              })}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/40 py-8 text-center text-xs text-muted-foreground">
        <p>
          © {new Date().getFullYear()} Seif Rabie Sakr · Built with love &amp; science
        </p>
      </footer>
    </div>
  );
}
