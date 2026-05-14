import time
import winsound
import sys
import io
import ctypes
from pynput import keyboard

# Force UTF-8 encoding for the console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Windows API for layout detection
user32 = ctypes.windll.user32

def get_active_layout_id():
    """Returns the LCID (Language Code ID) of the active window's keyboard layout."""
    try:
        # Get the handle of the foreground window
        hwnd = user32.GetForegroundWindow()
        # Get the thread ID of the foreground window
        thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
        # Get the keyboard layout ID for that thread
        layout_id = user32.GetKeyboardLayout(thread_id)
        # Extract the language ID (lower 16 bits)
        lang_id = layout_id & 0xFFFF
        return lang_id
    except:
        return None

# Common Language IDs
LANG_ARABIC = 0x01 # Primary ID for Arabic (0x0401, 0x0801, etc)
LANG_ENGLISH = 0x09 # Primary ID for English (0x0409, 0x0809, etc)

# Mapping for Standard English (QWERTY) to Standard Arabic (Windows)
EN_TO_AR = {
    'q': 'ض', 'w': 'ص', 'e': 'ث', 'r': 'ق', 't': 'ف', 'y': 'غ', 'u': 'ع', 'i': 'ه', 'o': 'خ', 'p': 'ح', '[': 'ج', ']': 'د',
    'a': 'ش', 's': 'س', 'd': 'ي', 'f': 'ب', 'g': 'ل', 'h': 'ا', 'j': 'ت', 'k': 'ن', 'l': 'م', ';': 'ك', "'": 'ط',
    'z': 'ئ', 'x': 'ء', 'c': 'ؤ', 'v': 'ر', 'b': 'لا', 'n': 'ى', 'm': 'ة', ',': 'و', '.': 'ز', '/': 'ظ',
    'Q': 'َ', 'W': 'ً', 'E': 'ُ', 'R': 'ٌ', 'T': 'لإ', 'Y': 'إ', 'U': '‘', 'I': '÷', 'O': '×', 'P': '؛', '{': '<', '}': '>',
    'A': 'ِ', 'S': 'ٍ', 'D': ']', 'F': '[', 'G': 'لأ', 'H': 'أ', 'J': 'ـ', 'K': '،', 'L': '/', ':': ':', '"': '"',
    'Z': '~', 'X': 'ْ', 'C': '{', 'V': '}', 'B': 'لآ', 'N': 'آ', 'M': '’', '<': ',', '>': '.', '?': '؟'
}
AR_TO_EN = {v: k for k, v in EN_TO_AR.items()}

class KeyboardGuard:
    def __init__(self):
        self.buffer = []
        self.last_press_time = time.time()
        self.last_alert_time = 0 # To prevent multiple beeps
        
    def play_alert(self):
        # Prevent rapid-fire beeping
        if time.time() - self.last_alert_time < 2.0:
            return
            
        try:
            # A cleaner, more distinct double beep
            winsound.Beep(1200, 100)
            winsound.Beep(1600, 150)
            self.last_alert_time = time.time()
        except:
            pass

    def process_buffer(self):
        if len(self.buffer) < 3: return

        lang_id = get_active_layout_id()
        if lang_id is None: return
        
        primary_lang = lang_id & 0xFF
        
        raw_text = "".join(self.buffer).lower()
        interpreted_ar = "".join([EN_TO_AR.get(c, c) for c in self.buffer])
        interpreted_en = "".join([AR_TO_EN.get(c, c) for c in self.buffer]).lower()

        vowels = 'aeiouy'
        
        # --- Case 1: Layout is ENGLISH, but typing looks like Arabic ---
        if primary_lang == LANG_ENGLISH:
            has_vowel = any(c in vowels for c in raw_text)
            if not has_vowel and len(raw_text) >= 4:
                ar_chars = sum(1 for c in interpreted_ar if '\u0600' <= c <= '\u06FF')
                if ar_chars / len(raw_text) > 0.8:
                    print(f"[!] Mismatch: English mode, but typing Arabic.")
                    self.play_alert()
                    self.buffer = []

        # --- Case 2: Layout is ARABIC, but typing looks like English ---
        elif primary_lang == LANG_ARABIC:
            # Be more sensitive to common English words or vowel-heavy patterns
            en_has_vowel = any(c in vowels for c in interpreted_en)
            
            # Instant trigger for common short English words
            common_short = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'any', 'can', 'was'}
            if interpreted_en in common_short or any(interpreted_en.startswith(w) for w in common_short):
                print(f"[!] Mismatch: Arabic mode, but typing English word: {interpreted_en}")
                self.play_alert()
                self.buffer = []
                return

            # If it's 4+ characters and looks like English phonetics
            if len(interpreted_en) >= 4 and en_has_vowel:
                # Basic check: English words usually have a vowel every 1-3 letters
                # Arabic mapped to English vowels (h, i, u, o, a) is common, but 
                # English words follow specific patterns.
                if any(interpreted_en.startswith(p) for p in ('str', 'sch', 'ph', 'th', 'sh', 'ch')):
                    print(f"[!] Mismatch: Arabic mode, but typing English pattern.")
                    self.play_alert()
                    self.buffer = []

    def on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                if time.time() - self.last_press_time > 1.2:
                    self.buffer = []
                self.buffer.append(key.char)
                self.last_press_time = time.time()
                if len(self.buffer) >= 3:
                    self.process_buffer()
                if len(self.buffer) > 12:
                    self.buffer.pop(0)
            elif key == keyboard.Key.space or key == keyboard.Key.enter:
                self.buffer = []
            elif key == keyboard.Key.backspace:
                if self.buffer: self.buffer.pop()
        except:
            pass

    def run(self):
        print("Keyboard Guard SMART MODE active...")
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

if __name__ == "__main__":
    guard = KeyboardGuard()
    guard.run()
