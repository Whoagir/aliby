#!/usr/bin/env python3
"""
Add Russian translations to words_alias.json
Uses downloaded eng_rus_dict.json dictionary
"""
import json
from pathlib import Path

print("Loading EN-RU dictionary...")
with open('eng_rus_dict.json', 'r', encoding='utf-8') as f:
    eng_rus_dict = json.load(f)

print(f"Dictionary loaded: {len(eng_rus_dict)} entries")

print("\nLoading words_alias.json...")
DATA_DIR = Path("app/data")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    alias_data = json.load(f)

print("Translating words...")
translated_count = 0
untranslated = []
total_words = 0

for difficulty in ['easy', 'medium', 'hard', 'mixed']:
    words_list = alias_data[difficulty]
    print(f"\nProcessing {difficulty}: {len(words_list)} words")
    
    for word_obj in words_list:
        word = word_obj['word']
        word_lower = word.lower()
        total_words += 1
        
        # Try to find translation
        translation = None
        
        # Try UPPERCASE (dictionary format)
        word_upper = word.upper()
        if word_upper in eng_rus_dict:
            translations = eng_rus_dict[word_upper]
            # Take first translation if it's a list
            if isinstance(translations, list) and len(translations) > 0:
                translation = translations[0].lower().capitalize()
            elif isinstance(translations, str):
                translation = translations.lower().capitalize()
        
        # Try lowercase
        elif word_lower in eng_rus_dict:
            translations = eng_rus_dict[word_lower]
            if isinstance(translations, list) and len(translations) > 0:
                translation = translations[0].lower().capitalize()
            elif isinstance(translations, str):
                translation = translations.lower().capitalize()
        
        if translation:
            word_obj['translation'] = translation
            translated_count += 1
        else:
            word_obj['translation'] = ""
            if word_lower not in untranslated:
                untranslated.append(word_lower)

print(f"\n{'='*50}")
print(f"RESULTS:")
print(f"  Total words: {total_words}")
print(f"  Translated: {translated_count} ({translated_count*100//total_words}%)")
print(f"  Untranslated: {len(untranslated)} unique words")
print(f"{'='*50}")

print(f"\nFirst 100 untranslated words:")
for i, word in enumerate(sorted(untranslated)[:100], 1):
    print(f"{i:3}. {word}")

# Save updated words with translations
print("\n\nSaving words_alias.json with translations...")
with open(DATA_DIR / "words_alias.json", 'w', encoding='utf-8') as f:
    json.dump(alias_data, f, indent=2, ensure_ascii=False)

# Save untranslated list for manual work
print("Saving untranslated_words.txt...")
with open(DATA_DIR / "untranslated_words.txt", 'w', encoding='utf-8') as f:
    for word in sorted(untranslated):
        f.write(f"{word}\n")

print(f"\n✓ words_alias.json updated with translations")
print(f"✓ {DATA_DIR / 'untranslated_words.txt'} created")
print(f"\nNext steps:")
print(f"1. Review untranslated_words.txt ({len(untranslated)} words)")
print(f"2. Add manual translations if needed")
print(f"3. Or use Google Translate API for remaining words")
