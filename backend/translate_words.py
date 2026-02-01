#!/usr/bin/env python3
"""
Translate English words to Russian
Strategy:
1. Load existing words from words_alias.json
2. Try translating with free dictionary
3. List untranslated words for manual translation
"""
import json
from pathlib import Path

# Simple EN-RU dictionary for most common words
# Will expand this with a larger dictionary source
BASIC_TRANSLATIONS = {
    # Top 100 most common words
    "the": "определенный артикль",
    "be": "быть",
    "to": "к",
    "of": "из",
    "and": "и",
    "a": "неопределенный артикль",
    "in": "в",
    "that": "что",
    "have": "иметь",
    "it": "это",
    "for": "для",
    "not": "не",
    "on": "на",
    "with": "с",
    "he": "он",
    "as": "как",
    "you": "ты",
    "do": "делать",
    "at": "в",
    "this": "это",
    "but": "но",
    "his": "его",
    "by": "по",
    "from": "от",
    "they": "они",
    "we": "мы",
    "say": "говорить",
    "her": "её",
    "she": "она",
    "or": "или",
    "an": "неопределенный артикль",
    "will": "будет",
    "my": "мой",
    "one": "один",
    "all": "все",
    "would": "бы",
    "there": "там",
    "their": "их",
    "what": "что",
    "so": "так",
    "up": "вверх",
    "out": "вне",
    "if": "если",
    "about": "о",
    "who": "кто",
    "get": "получать",
    "which": "который",
    "go": "идти",
    "me": "меня",
    "when": "когда",
    "make": "делать",
    "can": "мочь",
    "like": "нравиться",
    "time": "время",
    "no": "нет",
    "just": "только",
    "him": "его",
    "know": "знать",
    "take": "брать",
    "people": "люди",
    "into": "в",
    "year": "год",
    "your": "твой",
    "good": "хороший",
    "some": "некоторый",
    "could": "мог",
    "them": "их",
    "see": "видеть",
    "other": "другой",
    "than": "чем",
    "then": "тогда",
    "now": "сейчас",
    "look": "смотреть",
    "only": "только",
    "come": "приходить",
    "its": "его",
    "over": "над",
    "think": "думать",
    "also": "также",
    "back": "назад",
    "after": "после",
    "use": "использовать",
    "two": "два",
    "how": "как",
    "our": "наш",
    "work": "работа",
    "first": "первый",
    "well": "хорошо",
    "way": "путь",
    "even": "даже",
    "new": "новый",
    "want": "хотеть",
    "because": "потому что",
    "any": "любой",
    "these": "эти",
    "give": "давать",
    "day": "день",
    "most": "большинство",
    "us": "нас",
}

print("Loading words_alias.json...")
DATA_DIR = Path("app/data")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    alias_data = json.load(f)

print("Translating words...")
translated_count = 0
untranslated = []

for difficulty in ['easy', 'medium', 'hard', 'mixed']:
    words_list = alias_data[difficulty]
    for word_obj in words_list:
        word = word_obj['word'].lower()
        
        if word in BASIC_TRANSLATIONS:
            word_obj['translation'] = BASIC_TRANSLATIONS[word]
            translated_count += 1
        else:
            word_obj['translation'] = ""  # Empty for now
            untranslated.append(word)

print(f"\nTranslated: {translated_count} words")
print(f"Untranslated: {len(untranslated)} words")
print(f"\nFirst 50 untranslated words:")
print(untranslated[:50])

# Save updated words
print("\nSaving updated words_alias.json...")
with open(DATA_DIR / "words_alias_with_translations.json", 'w', encoding='utf-8') as f:
    json.dump(alias_data, f, indent=2, ensure_ascii=False)

# Save untranslated list
with open(DATA_DIR / "untranslated_words.txt", 'w', encoding='utf-8') as f:
    for word in sorted(set(untranslated)):
        f.write(f"{word}\n")

print(f"✓ Saved to words_alias_with_translations.json")
print(f"✓ Untranslated words list saved to untranslated_words.txt")
print("\nNext steps:")
print("1. Use online translator API to translate remaining words")
print("2. Or manually translate untranslated_words.txt")
print("3. Merge translations back to words_alias.json")
