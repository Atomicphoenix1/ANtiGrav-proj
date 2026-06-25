import re
import html

TATWEEL = "\u0640"

DIACRITICS = str.maketrans({
    "\u064B": None,  # Fathatayn
    "\u064C": None,  # Dammatayn
    "\u064D": None,  # Kasratayn
    "\u064E": None,  # Fatha
    "\u064F": None,  # Damma
    "\u0650": None,  # Kasra
    "\u0651": None,  # Shadda
    "\u0652": None,  # Sukun
})

CHAR_MAP = str.maketrans({
    "\u0623": "\u0627",  # أ -> ا
    "\u0625": "\u0627",  # إ -> ا
    "\u0622": "\u0627",  # آ -> ا
    "\u0671": "\u0627",  # ٱ -> ا
    "\u0629": "\u0647",  # ة -> ه
    "\u0649": "\u064A",  # ى -> ي
})

HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return HTML_TAG_RE.sub("", text)


def normalize(text: str) -> str:
    text = html.unescape(text)
    text = strip_html(text)
    text = text.replace(TATWEEL, "")
    text = text.translate(DIACRITICS)
    text = text.translate(CHAR_MAP)
    text = re.sub(r"\s+", " ", text).strip()
    return text
