# Scheduling & Personnel Automation

A visual coordination engine that transforms the tedious process of finding common availability into a streamlined, one-minute task.

## ⚙️ How it Works

### 1. Data Collection (Google Forms/Sheets)
- **Mechanism:** Participants submit their availability via a standard Google Form.
- **n8n Trigger:** An n8n workflow (`المواعيد.json`) monitors the Google Sheet for new responses.

### 2. The Logic Engine (`المواعيد.json`)
- **Action:** Processes raw timestamp data and availability strings.
- **Logic:** Aggregates availability density across the team. It identifies overlap "hotspots" where the maximum number of personnel are free.
- **Output:** Passes the cleaned, aggregated data to a visual frontend.

### 3. The Visual Interface (`final_task_board_with_anas.html`)
- **Mechanism:** An interactive HTML/JavaScript dashboard.
- **Features:**
  - **Density Visualization:** Instantly see which times have the most available participants.
  - **Dynamic Filters:** Hide/Show specific participants to see how they impact the schedule.
  - **Top 4 Recommendations:** The UI automatically highlights the four best time slots based on the highest availability density.

## 📊 Impact
- **Manual Workflow:** 30–45 minutes of checking spreadsheets and filtering.
- **ANtiGrav Workflow:** **< 2 minutes**.
- **Result:** 95%+ reduction in administrative overhead.

---
*Part of the ANtiGrav Automation Suite.*
