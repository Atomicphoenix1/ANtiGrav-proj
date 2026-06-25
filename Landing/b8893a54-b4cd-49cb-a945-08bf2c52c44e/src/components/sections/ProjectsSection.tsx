import { projects } from "@/data/portfolioData";
import { ProjectCard } from "@/components/ProjectCard";

export function ProjectsSection() {
  return (
    <section aria-labelledby="projects-heading">
      <h2
        id="projects-heading"
        className="mb-8 font-heading text-2xl font-bold tracking-tight text-foreground"
      >
        Projects & Technical Undertakings
      </h2>
      <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3" role="list">
        {projects.map((project) => (
          <li key={project.id}>
            <ProjectCard project={project} />
          </li>
        ))}
      </ul>
    </section>
  );
}
