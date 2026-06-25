import time
import pyautogui
import subprocess

# 1. Launch the Antigravity desktop application directly
subprocess.Popen([r"C:\Path\To\Your\Antigravity.exe"])

# 2. Crucial pause: Give the app UI a moment to visually load and focus on your screen
time.sleep(10) 

# 3. Type "hi" smoothly using PyAutoGUI's keyboard controller
pyautogui.write("hi", interval=0.1)

# 4. Fire the Enter key to hit the chatbox "send" action trigger
pyautogui.press("enter")