#!/usr/bin/env python3
"""
Process Excel translations and apply to words_alias.json
"""
import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path("app/data")
TRANSLATE_DIR = DATA_DIR / "translate"

print("Loading Excel files...")

translations = {}

# Load EASY
easy_file = TRANSLATE_DIR / "easy.xlsx"
if easy_file.exists():
    df = pd.read_excel(easy_file)
    print(f"\nEASY file columns: {df.columns.tolist()}")
    print(f"EASY rows: {len(df)}")
    
    # Detect column names (flexible)
    word_col = None
    trans_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'word' in col_lower and not word_col:
            word_col = col
        elif 'trans' in col_lower or 'перевод' in col_lower:
            trans_col = col
    
    if not word_col:
        word_col = df.columns[0]
    if not trans_col:
        trans_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    print(f"Using columns: word='{word_col}', translation='{trans_col}'")
    
    for _, row in df.iterrows():
        # Check if data is in CSV format in one column
        cell_value = str(row[word_col]).strip()
        
        if ',' in cell_value:
            # Split CSV format: "word,translation"
            parts = cell_value.split(',', 1)
            if len(parts) == 2:
                word = parts[0].strip()
                translation = parts[1].strip()
            else:
                continue
        else:
            word = str(row[word_col]).strip()
            translation = str(row[trans_col]).strip() if word_col != trans_col else ''
        
        if word and translation and word != 'nan' and translation != 'nan' and translation != '':
            translations[word] = translation
    
    print(f"✓ Loaded {len([k for k, v in translations.items()])} EASY translations")

# Load MEDIUM
medium_file = TRANSLATE_DIR / "middle.xlsx"
if medium_file.exists():
    df = pd.read_excel(medium_file)
    print(f"\nMEDIUM file columns: {df.columns.tolist()}")
    print(f"MEDIUM rows: {len(df)}")
    
    # Detect columns
    word_col = None
    trans_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'word' in col_lower and not word_col:
            word_col = col
        elif 'trans' in col_lower or 'перевод' in col_lower:
            trans_col = col
    
    if not word_col:
        word_col = df.columns[0]
    if not trans_col:
        trans_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    print(f"Using columns: word='{word_col}', translation='{trans_col}'")
    
    before_count = len(translations)
    for _, row in df.iterrows():
        # Check if data is in CSV format in one column
        cell_value = str(row[word_col]).strip()
        
        if ',' in cell_value:
            # Split CSV format: "word,translation"
            parts = cell_value.split(',', 1)
            if len(parts) == 2:
                word = parts[0].strip()
                translation = parts[1].strip()
            else:
                continue
        else:
            word = str(row[word_col]).strip()
            translation = str(row[trans_col]).strip() if word_col != trans_col else ''
        
        if word and translation and word != 'nan' and translation != 'nan' and translation != '':
            if word not in translations:  # Avoid duplicates
                translations[word] = translation
    
    new_count = len(translations) - before_count
    print(f"✓ Loaded {new_count} MEDIUM translations (duplicates removed)")

print(f"\n📊 Total unique translations: {len(translations)}")

if not translations:
    print("❌ No translations found!")
    exit(1)

# Show sample
print(f"\n📝 Sample translations:")
for word, trans in list(translations.items())[:10]:
    print(f"  {word} → {trans}")

# Apply to words_alias.json
print(f"\nLoading words_alias.json...")
with open(DATA_DIR / "words_alias.json", 'r', encoding='utf-8') as f:
    alias_data = json.load(f)

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

print(f"\n✅ SUCCESS!")
print(f"  • {len(translations)} unique translations")
print(f"  • {applied_count} applications (with duplicates in mixed)")
print(f"  • Backup saved")

# Calculate coverage
total_words = sum(len(alias_data[d]) for d in ['easy', 'medium', 'hard', 'mixed'])
words_with_translation = 0
for difficulty in ['easy', 'medium', 'hard', 'mixed']:
    for word_obj in alias_data[difficulty]:
        if word_obj.get('translation') and word_obj['translation'] != '':
            words_with_translation += 1

coverage = (words_with_translation / total_words) * 100
print(f"\n📈 Coverage: {words_with_translation}/{total_words} ({coverage:.1f}%)")
