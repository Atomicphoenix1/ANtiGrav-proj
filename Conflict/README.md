# Conflict Resolver Timeline

Welcome to the Conflict Resolver Timeline! This is a completely standalone application that runs entirely in your browser. You do not need to install Node, React, or any software.

## 🚀 How to Run
1. Simply double-click the **`schedule.html`** file.
2. It will open in your default web browser (Chrome, Edge, Safari, etc.).
3. Click the **"Push Data"** button at the top right to pull in the live schedule data.

---

## 🔗 Connecting Your Own Data (The Webhook Link)

By default, this application tries to pull data from a specific n8n webhook URL. If you want to connect this timeline to your own n8n instance or Google Sheet, you need to change the link!

### Step 1: Find the URL in the Code
1. Right-click on **`schedule.html`** and open it with any text editor (like Notepad, VS Code, or TextEdit).
2. Scroll down to approximately **Line 33** (right after the icons).
3. Look for this line:
   ```javascript
   const N8N_WEBHOOK_URL = 'https://curtsy-electable-schilling.ngrok-free.dev/webhook-test/5d7bdaf1-f375-459e-b6e9-a73cb24c42f5';
   ```

### Step 2: Replace the URL
1. Delete the old URL inside the quotes.
2. Paste your own n8n Webhook URL.
   *(Make sure you keep the single quotes around the link!)*
3. Save the file.

### Step 3: Ensure Your n8n Output Matches
Your n8n webhook should output a JSON array from your Google Sheet. The app is incredibly smart and will look for the following column names in your data:

- **Name Column**: It checks for `الاسم`, `name`, `participant`, or `user`.
- **Timing Columns**: It checks for `موعد 1`, `موعد 2`, `موعد 3`, `موعد 4`, `موعد 5`, and `موعد 6`. 
  - *Tip:* You can write times in plain English in your spreadsheet! For example, typing `"9 to 12"` or `"09:00 - 12:00"` will automatically extract the numbers and draw a block on the timeline from 9 AM to 12 PM.

---

## 🎨 Modifying the Theme or Colors
If you want to change the colors of the user blocks, open `schedule.html` in a text editor and look for:
```javascript
const COLORS = ['#6366f1', '#ec4899', '#10b981', '#f59e0b', '#06b6d4', '#8b5cf6'];
```
You can replace those Hex codes with any colors you like!
