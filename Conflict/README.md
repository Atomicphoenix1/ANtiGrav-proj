# Scheduling & Personnel Automation (Deterministic Visual Engine)

This project transforms complex, unstructured personnel availability into a clean, visual management system. It avoids AI hallucinations by using **deterministic logic** to map variable time strings into standardized scheduling blocks.

## ⚙️ The Mechanism

### 1. Data Collection (Input)
- **Source:** Participants submit their availability via a Google Form.
- **Complexity:** The form accepts variable strings such as **dawn/evening** (e.g., Maghrib, Isha) or specific ranges (e.g., 8:00 AM - 9:00 PM).
- **Storage:** All responses are automatically saved to a Google Sheet.

### 2. Standardization & Logic Engine
- **Processing:** An n8n workflow retrieves the strings and applies standardized mapping codes.
- **Deterministic Mapping:** Every input string is converted into a specific, hard-coded time block. This ensures **zero AI hallucinations** and 100% accuracy in data representation.
- **Payload:** The standardized data is pushed to a custom UI.

### 3. Visual Interactive Dashboard (HTML/JS)
The frontend application provides a high-level management view with several key features:
- **Density Heatmaps:** Instantly visualize which time slots have the highest number of participants.
- **Top 4 Recommendations:** The system automatically highlights the four best time slots based on maximum availability.
- **Dynamic Filters:** Users can "hide" or "show" specific participants to see how they affect the schedule.
- **Manual Overrides:** Managers can edit times directly on the site for final fine-tuning.

## 📊 Impact
- **Efficiency Gain:** Reduced a 45-minute manual coordination task to a **mere 60-90 seconds**.
- **Accuracy:** Eliminated human and AI errors through structured data transformation.

---
*Developed as part of the ANtiGrav Automation Series.*
