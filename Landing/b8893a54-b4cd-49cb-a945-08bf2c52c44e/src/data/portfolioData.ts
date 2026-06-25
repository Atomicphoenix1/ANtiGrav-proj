// ─── Portfolio Data ─────────────────────────────────────────────────────────
// Single source of truth. Edit here to update all sections of the site.
// Tab labels, section order, and content are all driven from this file.

export interface SocialLink {
  label: string;
  url: string;
  icon: "github" | "email" | "phone" | "location";
}

export interface Tab {
  id: string;
  /** Change this label to rename the tab in the navigation */
  label: string;
  /** Section IDs to render inside this tab, in order */
  sectionIds: Array<"projects" | "skills" | "education" | "experience">;
}

export interface WorkExperience {
  id: string;
  role: string;
  company: string;
  period: string;
  bullets: string[];
}

export interface EducationEntry {
  id: string;
  degree: string;
  concentration?: string;
  institution: string;
  location: string;
  period: string;
  status: string;
  gpa?: string;
  honors?: string[];
  coursework?: { category: string; items: string[] }[];
}

export interface SkillGroup {
  category: string;
  items: string[];
}

export interface CodePreviewConfig {
  language: string;
  /** Safe display-only pseudocode — actual logic stays server-side */
  displayCode: string;
  mockOutput: string;
}

export interface Project {
  id: string;
  title: string;
  description: string;
  techStack: string[];
  audioSrc?: string;
  codePreview?: CodePreviewConfig;
  links?: { label: string; url: string }[];
}

// ─── Personal ────────────────────────────────────────────────────────────────

export const personal = {
  name: "Seif Rabie Sakr",
  title: "Nano Scientist & AI Educator",
  tagline:
    "Bridging rigorous scientific training with AI-powered automation and high-energy STEM education.",
  location: "Alexandria, Egypt",
  socials: [
    { label: "s-seif.sakr@zewailcity.edu.eg", url: "mailto:s-seif.sakr@zewailcity.edu.eg", icon: "email" },
    { label: "seefraber31@gmail.com", url: "mailto:seefraber31@gmail.com", icon: "email" },
    { label: "+20 121 257 8915", url: "tel:+201212578915", icon: "phone" },
    { label: "GitHub", url: "https://github.com/", icon: "github" },
    { label: "Alexandria, Egypt", url: "#", icon: "location" },
  ] satisfies SocialLink[],
  welcomeAudioSrc: "/audio/welcome.mp3",
};

// ─── Tabs ─────────────────────────────────────────────────────────────────────
// Rename `label` to give each tab a meaningful name.
// Reorder `sectionIds` to change what appears in each tab.

export const tabs: Tab[] = [
  {
    id: "tab-one",
    label: "TabOne",
    sectionIds: ["projects"],
  },
  {
    id: "tab-two",
    label: "TabTwo",
    sectionIds: ["skills", "education"],
  },
  {
    id: "tab-three",
    label: "TabThree",
    sectionIds: ["experience"],
  },
];

// ─── Projects ────────────────────────────────────────────────────────────────

export const projects: Project[] = [
  {
    id: "transcription-pipeline",
    title: "AI Transcription Pipeline",
    description:
      "End-to-end automated transcription pipeline using AI tools to process audio records into formatted Word Docs/PDFs, then distribute them hands-free to Telegram channels.",
    techStack: ["AI Studio", "Anti-gravity", "n8n", "Telegram API"],
    audioSrc: "/audio/projects/transcription-pipeline.mp3",
    codePreview: {
      language: "python",
      displayCode: `# AI Transcription Pipeline — workflow orchestrator
# (execution logic runs server-side)

def run_pipeline(audio_source: str) -> PipelineResult:
    audio  = validate_source(audio_source)
    text   = transcribe(audio)           # → AI transcription
    doc    = format_document(text)       # → DOCX / PDF
    result = distribute(doc, channels)   # → Telegram
    return PipelineResult(status="ok", words=len(text.split()))`,
      mockOutput: `[Pipeline] Initialized…
[Pipeline] Audio source validated ✓
[Pipeline] Transcription complete — 847 words
[Pipeline] Formatting to DOCX…
[Pipeline] Dispatching to Telegram channel ✓

Status : SUCCESS
Duration: 5.2 s
Words   : 847`,
    },
  },
  {
    id: "scheduling-automation",
    title: "Scheduling & Personnel Automation",
    description:
      "Visual scheduling application connecting Google Forms to an HTML UI via n8n. Reduced slot coordination from a 45-minute manual process to under 2 minutes — a 95%+ efficiency gain.",
    techStack: ["n8n", "Google Forms", "HTML/CSS", "JavaScript"],
    audioSrc: "/audio/projects/scheduling-automation.mp3",
    codePreview: {
      language: "javascript",
      displayCode: `// Scheduling optimizer — slot ranking engine
// (core algorithm runs server-side)

async function optimizeSlots(formResponses) {
  const availability = parseResponses(formResponses);
  const densityMap   = buildDensityMap(availability);
  const topSlots     = rankSlots(densityMap, { topN: 4 });

  return topSlots.map(slot => ({
    time:         slot.label,
    participants: slot.count,
    coverage:     \`\${slot.pct}%\`,
  }));
}`,
      mockOutput: `[Scheduler] Loading 23 participant responses…
[Scheduler] Building availability density map…
[Scheduler] Running slot optimization…

TOP 4 OPTIMAL SLOTS:
  1. Mon 10:00–11:00 → 19 participants (82%)
  2. Wed 14:00–15:00 → 17 participants (73%)
  3. Thu 09:00–10:00 → 15 participants (65%)
  4. Fri 11:00–12:00 → 14 participants (60%)

Optimization complete in 0.08 s  (prev: 45 min manual)`,
    },
  },
  {
    id: "computational-chemistry",
    title: "Computational Chemistry & Nanomaterial Characterization",
    description:
      "Quantum chemistry calculations using Gaussian software, plus lab synthesis and characterization of AgNPs, AuNPs, Lipid NPs, SPIONs, and Micelles using AFM/STM microscopy techniques.",
    techStack: ["Gaussian 16", "DFT/B3LYP", "AFM", "STM", "Python"],
    audioSrc: "/audio/projects/computational-chemistry.mp3",
    codePreview: {
      language: "python",
      displayCode: `# Gaussian job submission wrapper
# (HPC execution runs server-side)

def submit_gaussian_job(molecule: Molecule) -> JobResult:
    config = GaussianConfig(
        method   = "B3LYP",
        basis    = "LANL2DZ",
        solvation= "PCM",
        solvent  = "water",
    )
    job    = build_input_file(molecule, config)
    result = run_on_cluster(job)   # → remote HPC call
    return parse_output(result)`,
      mockOutput: `Gaussian 16 Rev. C.01 — Job Summary
=====================================
Molecule  : AgNP cluster (147 atoms)
Method    : DFT/B3LYP/LANL2DZ
Solvation : PCM (water)

Energy (SCF)  : -12847.3921 Hartree
Dipole moment : 0.0023 Debye
HOMO-LUMO gap : 2.87 eV

Output → output/agnp_147_results.log
Status  : Converged in 42 cycles ✓`,
    },
  },
];

// ─── Skills ───────────────────────────────────────────────────────────────────

export const skills: SkillGroup[] = [
  {
    category: "AI & Automation",
    items: ["Prompt-based Automation", "n8n Workflow Design", "Agentic AI Pipelines"],
  },
  {
    category: "Programming",
    items: ["Python (Fundamentals, Code Reading, Debugging)"],
  },
  {
    category: "Scientific",
    items: [
      "Computational Chemistry (Gaussian)",
      "Nanomaterial Synthesis (AgNPs, AuNPs, SPIONs)",
      "Material Characterization (AFM / STM)",
    ],
  },
  {
    category: "Languages",
    items: ["Arabic (Native)", "English (Professional Working Proficiency)"],
  },
];

// ─── Education ────────────────────────────────────────────────────────────────

export const education: EducationEntry[] = [
  {
    id: "zewail-city",
    degree: "Bachelor of Science in Nano Science",
    concentration: "Nanophysics",
    institution: "University of Science and Technology at Zewail City",
    location: "Giza, Egypt",
    period: "Expected July 2026",
    status: "Junior Student",
    gpa: "3.825 / 4.00",
    honors: ["Provost's Honors Roll (Multiple Semesters)"],
    coursework: [
      {
        category: "Nano Science",
        items: ["Synthesis/Fabrication of Nanomaterials", "Modern Characterization Techniques"],
      },
      {
        category: "Physics",
        items: ["Quantum Mechanics I", "Electrodynamics I", "Mathematical Physics I", "Wave Motion & Optics"],
      },
      {
        category: "Mathematics & CS",
        items: ["Linear Algebra & Vector Geometry", "Ordinary Differential Equations", "Intro to Computer Science"],
      },
    ],
  },
];

// ─── Experience ───────────────────────────────────────────────────────────────

export const experience: WorkExperience[] = [
  {
    id: "bonyan-instructor",
    role: "Programming & AI Instructor",
    company: "Bonyan",
    period: "August 2025 – April 2026",
    bullets: [
      "Instructed 29+ unique students (ages 6–17) in focused groups of up to 6, fostering high-energy, engagement-first learning.",
      "Delivered multi-level curriculum: Scratch (12 students), AI Level 1 — PictoBlox/Back to Blocks (13 students), AI Level 2 — Python-based (8 students), Mobile App Development — MIT App Inventor (4 students).",
      "Guided students from visual block-based logic (Scratch/PictoBlox) to text-based Python programming.",
      "Led immersive Trial Sessions with a charismatic teaching style, consistently converting newcomers into long-term motivated students.",
    ],
  },
  {
    id: "freelance-tutor",
    role: "University Science & Mathematics Tutor",
    company: "Independent / Freelance",
    period: "March 2026 – Present",
    bullets: [
      "Tutored university engineering students in foundational sciences — Physics (EM2, Vector Mechanics) and Engineering Chemistry.",
    ],
  },
];
