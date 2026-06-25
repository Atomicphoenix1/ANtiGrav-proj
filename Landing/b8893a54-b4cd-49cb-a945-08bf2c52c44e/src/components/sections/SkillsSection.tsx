import { skills } from "@/data/portfolioData";

export function SkillsSection() {
  return (
    <section aria-labelledby="skills-heading">
      <h2
        id="skills-heading"
        className="mb-8 font-heading text-2xl font-bold tracking-tight text-foreground"
      >
        Technical Skills & Core Competencies
      </h2>
      <div className="grid gap-6 sm:grid-cols-2">
        {skills.map((group) => (
          <div
            key={group.category}
            className="rounded-2xl border border-border bg-card p-6"
          >
            <h3 className="mb-4 text-xs font-semibold uppercase tracking-[0.15em] text-accent">
              {group.category}
            </h3>
            <ul className="flex flex-col gap-2.5">
              {group.items.map((item) => (
                <li
                  key={item}
                  className="flex items-start gap-2 text-sm text-card-foreground"
                >
                  <span
                    className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
                    aria-hidden="true"
                  />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
