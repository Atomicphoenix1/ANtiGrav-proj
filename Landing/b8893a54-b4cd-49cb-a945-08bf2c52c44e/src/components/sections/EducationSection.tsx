import { GraduationCap, Award } from "lucide-react";
import { education } from "@/data/portfolioData";

export function EducationSection() {
  return (
    <section aria-labelledby="education-heading">
      <h2
        id="education-heading"
        className="mb-8 font-heading text-2xl font-bold tracking-tight text-foreground"
      >
        Education
      </h2>

      <div className="flex flex-col gap-6">
        {education.map((entry) => (
          <article
            key={entry.id}
            className="rounded-2xl border border-border bg-card p-6 shadow-sm"
          >
            {/* Header */}
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10">
                <GraduationCap className="h-5 w-5 text-accent" aria-hidden="true" />
              </div>
              <div className="flex-1">
                <h3 className="font-heading text-base font-semibold text-card-foreground">
                  {entry.degree}
                  {entry.concentration && (
                    <span className="font-normal text-muted-foreground">
                      {" "}— {entry.concentration}
                    </span>
                  )}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {entry.institution} · {entry.location}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {entry.status} · {entry.period}
                </p>
              </div>

              {/* GPA badge */}
              {entry.gpa && (
                <div className="shrink-0 rounded-lg bg-accent px-3 py-1.5 text-center">
                  <p className="text-xs font-semibold text-accent-foreground">GPA</p>
                  <p className="font-heading text-sm font-bold text-accent-foreground">
                    {entry.gpa}
                  </p>
                </div>
              )}
            </div>

            {/* Honors */}
            {entry.honors && entry.honors.length > 0 && (
              <ul className="mt-4 flex flex-wrap gap-2" aria-label="Honors">
                {entry.honors.map((honor) => (
                  <li
                    key={honor}
                    className="flex items-center gap-1.5 rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground"
                  >
                    <Award className="h-3 w-3 text-accent" aria-hidden="true" />
                    {honor}
                  </li>
                ))}
              </ul>
            )}

            {/* Coursework */}
            {entry.coursework && entry.coursework.length > 0 && (
              <div className="mt-5 border-t border-border/50 pt-5">
                <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                  Selected Coursework
                </h4>
                <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {entry.coursework.map((cw) => (
                    <div key={cw.category}>
                      <dt className="mb-1.5 text-xs font-semibold text-accent">
                        {cw.category}
                      </dt>
                      <dd>
                        <ul className="flex flex-col gap-1">
                          {cw.items.map((item) => (
                            <li
                              key={item}
                              className="flex items-start gap-1.5 text-xs text-muted-foreground"
                            >
                              <span
                                className="mt-1 h-1 w-1 shrink-0 rounded-full bg-muted-foreground/50"
                                aria-hidden="true"
                              />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
