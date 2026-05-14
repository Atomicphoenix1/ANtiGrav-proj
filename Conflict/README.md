# Personnel Management & Scheduling Automation

This tool transforms the process of finding common availability into a streamlined, one-minute task. It is designed to handle unstructured time data and provide clear visual recommendations.

## ⚙️ The Mechanism

### 1. Input: Google Forms & Sheets
- **Source:** Participants submit their availability via a **Google Form** using a checkbox-based interface.
- **Data:** The responses are saved to a **Google Sheet**. These often include string-based time periods such as **المغرب للعيشة** (Maghrib to Isha) or specific day ranges.

### 2. Logic: n8n Integration
- **Retrieval:** An **n8n** workflow retrieves the checkbox data from the Google Sheet.
- **Standardization:** The workflow maps these variable strings into standardized time codes. This ensures that a human-readable time like "Evening" corresponds exactly to a specific visual block on the dashboard.
- **Payload:** The cleaned and aggregated data is then pushed to the visual application.

### 3. Frontend: Visual Interactive Dashboard
The final dashboard provides several high-impact features for managers:
- **Heatmaps:** Instantly see time-slot "density" (where the most people are free).
- **Filters:** Toggle specific participants on or off to see how it impacts the group availability.
- **Top 4 Recommendations:** The system automatically highlights the four best time slots for the group.
- **Manual Adjustments:** Allows for fine-tuning times directly within the UI.

## 📊 Impact
- **Manual Workflow:** 30–45 minutes of manual cross-referencing.
- **Automated Workflow:** **< 2 minutes**.
- **Efficiency:** 95%+ reduction in coordination overhead.

---
*Developed as part of the ANtiGrav Automation Series.*
