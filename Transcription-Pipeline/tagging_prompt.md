# Tagging Prompt for Islamic Lecture Transcription (Final Version)

## Your Task

You will receive the raw text of an Islamic lecture transcription. Your job is to **add semantic tags** to it so that it can be processed by an automated formatting pipeline. You must follow the rules below **exactly and without exception**. Do not add commentary, explanations, or any text outside the tagged output.

---

## Rules

### 1. Full Diacritization (Tashkeel)
Every single Arabic word in the output must be **fully diacritized** (with tashkeel). This applies to all text regardless of tag type.

### 2. Speaker Tags — `<speaker>`
Wrap the speaker introduction line in `<speaker>` tags.
- **Commentator (الشارح):** `<speaker>قَالَ الشَّارِحُ هَدَاهُ اللَّهُ:</speaker>`
- **Author (المصنف):** `<speaker>قَالَ الْمُصَنِّفُ حَفِظَهُ اللَّهُ:</speaker>`

### 3. Matn Tags — `<matn>`
Wrap the body text spoken by the Author in `<matn>` tags.
```
<speaker>قَالَ الْمُصَنِّفُ حَفِظَهُ اللَّهُ:</speaker>
<matn>
[Text here]
</matn>
```

### 4. Hadith Tags — `<hadith>`
Wrap Prophetic narrations in `<hadith>` tags, with the text in square brackets `[...]`.
**IMPORTANT:** This applies even to **partial quotes** or when the Sheikh refers back to a specific phrase from a hadith. If it is a Prophetic word, it must be tagged.
**Example:** `وَفِي قَوْلِهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ: <hadith>[فَهُوَ رَدٌّ]</hadith>`

### 5. Quranic Verse Tags — `<quran>`
Wrap verses in `<quran>` tags with decorative brackets `﴿...﴾`.
**Example:** `<quran>﴿إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ﴾</quran>`

### 6. Book Titles & Scholar Quotes — `[...]`
Wrap book names and quotes from scholars/poets in **plain square brackets** with NO tags.
- Book: `فِي [مُغْنِي اللَّبِيبِ]`
- Quote: `قَالَ الْمُتَنَبِّي: [وَبِضِدِّهَا تَتَبَيَّنُ الْأَشْيَاءُ]`

### 7. Bold List Labels — `<strong>`
Wrap common enumeration labels in `<strong>` tags.
- `<strong>أَحَدُهُمَا:</strong>`
- `<strong>وَالآخَرُ:</strong>`
- `<strong>أَوَّلُهَا:</strong>`

### 8. Bullet Points — Dash `- `
Prefix every list item with `- ` (dash and space).

### 9. Honorifics — Plain Text
Leave phrases like `صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ` and `تَعَالَى` as plain diacritized text. Do not add tags.

---

## Critical Rules
1. **Never nest tags.**
2. **Never omit tashkeel.**
3. **No commentary in output.**
4. **Always ensure the <matn> tag covers the full paragraph of the Author's text.**
