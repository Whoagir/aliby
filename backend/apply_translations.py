#!/usr/bin/env python3
"""
Apply translations from CSV back to words_alias.json
"""
import json
import csv
from pathlib import Path

DATA_DIR = Path("app/data")

print("Loading untranslated_words.csv...")
translations = {}

try:
    with open(DATA_DIR / "untranslated_words.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row['word']
            translation = row['translation'].strip()
            if translation:  # Only add if translation provided
                translations[word] = translation
    
    print(f"Loaded {len(translations)} translations from CSV")
except FileNotFoundError:
    print("ERROR: untranslated_words.csv not found!")
    print("Please fill the CSV file first.")
    exit(1)

if not translations:
    print("No translations found in CSV. Please fill the 'translation' column.")
    exit(1)

print("\nLoading words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    alias_data = json.load(f)

# Apply translations
applied_count = 0
for difficulty in ['easy', 'medium', 'hard', 'mixed']:
    for word_obj in alias_data[difficulty]:
        word = word_obj['word']
        if word in translations:
            word_obj['translation'] = translations[word]
            applied_count += 1

print(f"Applied {applied_count} translations")

# Backup original file
backup_file = DATA_DIR / "words_alias_backup.json"
print(f"\nCreating backup: {backup_file}")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    backup_data = f.read()
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(backup_data)

# Save updated file
print("Saving updated words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'w', encoding='utf-8') as f:
    json.dump(alias_data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Done! Applied {applied_count} translations")
print(f"✓ Backup saved to {backup_file}")
print(f"\nNext step: Rebuild backend to load new translations")
print(f"  cd ~/projects/aliby && docker compose restart backend")
