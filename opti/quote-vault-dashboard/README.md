# 🌌 The Cosmic Alchemist's Quote Vault

Welcome to the **Cosmic Alchemist's Quote Vault**! This is a premium, distraction-free web dashboard designed for personal reflection. It dynamically cycles through your quotes, tracks your daily reflection streaks, lets you log custom thoughts/memories, and supports full n8n integrations.

---

## ⚡ Quick Start: How to Run
This application is designed to be **100% portable and offline-friendly**. It requires absolutely zero installation, servers, or terminal commands.

1.  **Unzip** the archive folder to your Desktop or any directory.
2.  **Double-click `index.html`** to launch it instantly in your favorite web browser (Chrome, Edge, Firefox, Brave, Safari).
3.  *Optional*: If you want to host it locally via a terminal, open a terminal inside this folder and run:
    ```bash
    python -m http.server 8000
    ```
    Then, navigate to `http://127.0.0.1:8000` in your web browser.

---

## 💻 Portability & Path Configurations
*   **Zero Absolute Paths**: All file paths inside the source code are strictly **relative** (`./style.css`, `./starfield.js`, `./app.js`). This means you and your friends can place this folder anywhere on any computer (Windows, macOS, or Linux) and it will load and render flawlessly without modifying any lines of code!
*   **Cloud CDN Integrations**: Lucide Icons and Google Fonts are loaded from secure, high-speed public Content Delivery Networks (CDNs) so you do not need to install local font packages. (An active internet connection is recommended during initial loading to fetch icons, although cached versions will work).
*   **Privacy & Local Storage**: All of your quotes, reflection history, streaks, and settings are saved completely locally inside your own browser's `LocalStorage` cache. Your entries are 100% private, secure, and never uploaded to any remote server!

---

## 🛠️ Key Features
*   **🌐 English & Arabic Interface (Bilingual)**: Smoothly toggle between English (LTR) and Arabic (RTL) mode with a single click. The UI dynamically changes fonts, layouts, and brackets to maintain visual excellence.
*   **🗄️ Isolated Local Storage**: English and Arabic quotes, streaks, and reflection chronicles are saved in completely isolated database namespaces. When you switch languages, your English archive and your Arabic archive stay perfectly separated!
*   **Orbit Focus Cycle**: Smart algorithm that loads and rotates quotes based on those you have seen the least or haven't viewed in a long time.
*   **Ember Streak Tracker**: Counts consecutive day visits. Check in daily to grow your reflection flame!
*   **Reflection Chronicles**: Track how your thoughts about a quote evolve. Write notes and realizations directly onto a localized, auto-timestamped timeline.
*   **Archive Search**: Real-time fuzzy filtering of all text, author, tags, and past reflections.
*   **Ambient soundscapes**: Click the floating musical bubble in the bottom right to start/stop serene cosmic synth chords.

---

## 🔗 How to Hook Up n8n Automation
If you would like to automatically send your quotes to Telegram, Notion, Discord, or email:
1.  Open your **n8n canvas**, create a new workflow, and add a **Webhook Node**.
2.  Set the webhook node's HTTP Method to **POST**.
3.  Copy the **Production Webhook URL** from the node.
4.  Open this dashboard, click the **Settings Gear Icon** in the top right.
5.  Paste your webhook URL into the input field, click **Test Connection**, and click **Save**.
6.  Click **Sync to n8n** on any quote card to instantly dispatch your wisdom and reflection logs to your active workflows!

---

### 🎨 Design Credits & Customization
This dashboard is powered by the **Cosmic Alchemist Style Kit**—a design fusion merging deep-space particle engines, glassmorphic glowing cards, and classical academic typography.

Feel free to open `style.css` to tweak primary colors:
*   `--neon-gold` (amber tones)
*   `--neon-cyan` (electric blue details)
*   `--neon-violet` (settings overlay glow)
