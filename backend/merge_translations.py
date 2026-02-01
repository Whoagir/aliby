#!/usr/bin/env python3
"""
Merge translations from priority files back to words_alias.json
"""
import json
import csv
from pathlib import Path

DATA_DIR = Path("app/data")

print("Loading translations from priority files...")
translations = {}

# Load from all priority files
for priority_file in ['to_translate_1_EASY.csv', 'to_translate_2_MEDIUM.csv', 'to_translate_3_HARD.csv']:
    filepath = DATA_DIR / priority_file
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row['word']
                translation = row['translation'].strip()
                if translation:
                    translations[word] = translation
        print(f"  {priority_file}: {sum(1 for k, v in translations.items() if v)} translations")

print(f"\nTotal translations loaded: {len(translations)}")

if not translations:
    print("No translations found. Please fill the CSV files first.")
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

# Backup
import shutil
backup_file = DATA_DIR / "words_alias_backup.json"
print(f"\nCreating backup: {backup_file}")
shutil.copy(DATA_DIR / "words_alias.json", backup_file)

# Save
print("Saving updated words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'w', encoding='utf-8') as f:
    json.dump(alias_data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Done! Applied {applied_count} translations")
print(f"✓ {len(translations)} unique words translated")
print(f"\n🔄 Next: Rebuild backend")
print(f"  cd ~/projects/aliby && docker compose restart backend")
