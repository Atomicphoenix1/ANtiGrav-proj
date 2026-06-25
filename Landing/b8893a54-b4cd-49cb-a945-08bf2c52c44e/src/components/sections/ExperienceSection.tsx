import { Briefcase } from "lucide-react";
import { experience } from "@/data/portfolioData";

export function ExperienceSection() {
  return (
    <section aria-labelledby="experience-heading">
      <h2
        id="experience-heading"
        className="mb-8 font-heading text-2xl font-bold tracking-tight text-foreground"
      >
        Professional Experience
      </h2>

      {/* Timeline */}
      <ol className="relative flex flex-col gap-0 border-s border-border ps-6">
        {experience.map((job, idx) => (
          <li key={job.id} className={idx < experience.length - 1 ? "pb-10" : ""}>
            {/* Timeline dot */}
            <span
              className="absolute -start-[11px] flex h-5 w-5 items-center justify-center rounded-full border-2 border-accent bg-background"
              aria-hidden="true"
            >
              <Briefcase className="h-2.5 w-2.5 text-accent" />
            </span>

            <article className="rounded-2xl border border-border bg-card p-6 shadow-sm">
              {/* Role + period */}
              <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h3 className="font-heading text-base font-semibold text-card-foreground">
                    {job.role}
                  </h3>
                  <p className="text-sm font-medium text-accent">{job.company}</p>
                </div>
                <span className="rounded-full bg-secondary px-3 py-1 text-xs font-medium text-muted-foreground">
                  {job.period}
                </span>
              </div>

              {/* Bullet points */}
              <ul className="flex flex-col gap-2.5">
                {job.bullets.map((bullet) => (
                  <li
                    key={bullet}
                    className="flex items-start gap-2.5 text-sm leading-relaxed text-muted-foreground"
                  >
                    <span
                      className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
                      aria-hidden="true"
                    />
                    {bullet}
                  </li>
                ))}
              </ul>
            </article>
          </li>
        ))}
      </ol>
    </section>
  );
}
