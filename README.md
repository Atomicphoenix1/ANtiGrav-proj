# ANtiGrav Projects Suite
**Practical Automation Solutions for Efficiency & Content Management**

This repository contains core automation tools designed to optimize complex logistical and administrative tasks using Python, n8n, and Anti-gravity.

## 🚀 Core Projects

### 1. [Conflict](./Conflict) (Personnel Management & Scheduling)
A visual coordination engine that transforms unstructured availability data into a clean, interactive dashboard.
- **How it Works:** Converts checkbox-based inputs and string-based availability (e.g., Arabic time periods like **المغرب للعيشة**) from **Google Forms/Sheets** into standardized blocks via **n8n**.
- **Key Outcome:** Reduced coordination time from 45 minutes to <2 minutes (95% efficiency gain).
- **Features:** Participant heatmaps, density visualization, and "Top 4" optimal time recommendations.

### 2. [Formatter_Final](./Formatter_Final) (Document Transcription & Formatting)
A structured workflow for converting audio lectures into publication-ready, scholarly documents.
- **How it Works:** A multi-stage pipeline that transcribes audio (AI Studio), tags structural elements, and formats via a custom Python engine using `.docx` templates.
- **Workflow Control:** Includes **n8n orchestration** with human-approval gates before Telegram distribution.
- **Key Outcome:** High-precision, RTL-aligned documents (Word/PDF) with consistent scholastic styling.

### 3. [n8nion](./n8nion) (Workflow Registry)
JSON exports for all published n8n workflows utilized across the ANtiGrav suite.

---

## 🛠️ Technical Philosophy
These projects focus on building **reliable, code-driven workflows**. While AI is used for transcription, the formatting, scheduling, and distribution logic are entirely structured and predictable to ensure total transparency.

---
*Developed by Seif Rabie Sakr.*
