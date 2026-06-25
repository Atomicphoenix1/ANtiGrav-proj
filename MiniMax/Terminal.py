import os
import time
import pyautogui

# 1. Open OpenCode TUI or Antigravity via Windows run command
os.system("start cmd /k opencode")  # Opens OpenCode in a new terminal
time.sleep(10)  # Wait for it to launch and focus

# 2. Click the chatbox area if needed, or if it autofocusses, just type
# (PyAutoGUI can also find a chatbox by looking at an image snippet)
pyautogui.write("hi", interval=0.1)

# 3. Press Enter to send
pyautogui.press("enter")