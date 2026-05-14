# ANtiGrav Projects Suite
**Deterministic Automation Solutions for High-Precision Workflows**

This repository contains a collection of code-driven automation tools designed to optimize complex logistical and administrative tasks. The suite focuses on ensuring **100% deterministic accuracy** by combining structured logic with modern integration tools.

## 🚀 Core Projects

### 1. [Conflict](./Conflict) (Deterministic Scheduling Engine)
A visual coordination dashboard that transforms variable, string-based availability into standardized scheduling blocks.
- **Mechanism:** Maps unstructured strings (e.g., Arabic time periods like "Maghrib") into hard-coded codes for precise UI representation.
- **Key Outcome:** Reduced coordination time from 45 minutes to <2 minutes (95% efficiency gain) with **zero AI hallucinations**.
- **Features:** Participant heatmaps, density visualization, and automated "Top 4" recommendations.

### 2. [Formatter_Final](./Formatter_Final) (Document Formatting Suite)
A 4-stage deterministic workflow for converting audio lectures into publication-ready, scholarly documents.
- **Mechanism:** A structured pipeline that transcribes audio (AI Studio), tags structural elements, formats via a custom Python engine using `.docx` templates, and manages distribution.
- **Workflow Control:** Includes **n8n orchestration** with human-approval gates before Telegram distribution.
- **Key Outcome:** High-precision, RTL-aligned documents (Word/PDF) with consistent scholastic styling and Islamic typography.

### 3. [n8nion](./n8nion) (Workflow Registry)
JSON exports for all published n8n workflows utilized across the ANtiGrav suite.

---

## 🛠️ Technical Philosophy
The projects in this suite are built on **deterministic orchestration**. While AI is utilized as a tool for the *initial transcription* phase in the document pipeline, all formatting, scheduling, and distribution logic is governed by structured code to ensure total reliability and transparency.

---
*Developed by Seif Rabie Sakr.*
