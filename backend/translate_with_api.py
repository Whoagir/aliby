#!/usr/bin/env python3
"""
Translate words using free translation API
Uses MyMemory Translation API (free, no key needed, 1000 requests/day per IP)
"""
import json
import time
import requests
from pathlib import Path

def translate_word(word, from_lang='en', to_lang='ru'):
    """Translate using MyMemory API"""
    url = f"https://api.mymemory.translated.net/get?q={word}&langpair={from_lang}|{to_lang}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data['responseStatus'] == 200:
            translation = data['responseData']['translatedText']
            # Clean up translation (take first word if multiple)
            translation = translation.strip().split(',')[0].split(';')[0]
            return translation
        return None
    except Exception as e:
        print(f"Error translating '{word}': {e}")
        return None

print("Loading words_alias.json...")
DATA_DIR = Path("app/data")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    alias_data = json.load(f)

print("Starting translation (this will take a while)...")
print("Translating up to 1000 words (API limit)")

translated_count = 0
failed_count = 0
total_processed = 0
max_translations = 1000  # API limit per day

# Collect all unique words first
unique_words = {}
for difficulty in ['easy', 'medium', 'hard', 'mixed']:
    for word_obj in alias_data[difficulty]:
        word = word_obj['word']
        if word not in unique_words:
            unique_words[word] = None

print(f"Total unique words to translate: {len(unique_words)}")

# Translate unique words (up to limit)
for i, word in enumerate(list(unique_words.keys())[:max_translations], 1):
    if i % 50 == 0:
        print(f"  Progress: {i}/{min(len(unique_words), max_translations)} words...")
    
    translation = translate_word(word)
    
    if translation:
        unique_words[word] = translation
        translated_count += 1
    else:
        failed_count += 1
    
    # Be nice to the API
    time.sleep(0.5)  # 500ms delay between requests

print(f"\nApplying translations to words_alias.json...")

# Apply translations to all difficulties
for difficulty in ['easy', 'medium', 'hard', 'mixed']:
    for word_obj in alias_data[difficulty]:
        word = word_obj['word']
        if word in unique_words and unique_words[word]:
            word_obj['translation'] = unique_words[word]
        else:
            word_obj['translation'] = ""

print(f"\n{'='*50}")
print(f"RESULTS:")
print(f"  Translated: {translated_count} unique words")
print(f"  Failed: {failed_count} words")
print(f"  Remaining: {len(unique_words) - max_translations} words (need another run)")
print(f"{'='*50}")

# Save updated words
backup_file = DATA_DIR / "words_alias_backup.json"
print(f"\nCreating backup: {backup_file}")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    backup_data = f.read()
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(backup_data)

print("Saving updated words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'w', encoding='utf-8') as f:
    json.dump(alias_data, f, indent=2, ensure_ascii=False)

# Save untranslated list
untranslated = [w for w in unique_words.keys() if not unique_words[w]]
print(f"Saving untranslated_words.txt ({len(untranslated)} words)...")
with open(DATA_DIR / "untranslated_words.txt", 'w', encoding='utf-8') as f:
    for word in sorted(untranslated):
        f.write(f"{word}\n")

print(f"\n✓ Done!")
print(f"\nSample translations:")
for word, translation in list(unique_words.items())[:10]:
    if translation:
        print(f"  {word} -> {translation}")
