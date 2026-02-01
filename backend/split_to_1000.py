#!/usr/bin/env python3
"""
Split MEDIUM and HARD files into 1000-word chunks
"""
import csv
from pathlib import Path

DATA_DIR = Path("app/data")

def split_file(input_file, prefix, chunk_size=1000):
    """Split CSV file into chunks"""
    words = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            words.append(row)
    
    total_words = len(words)
    total_chunks = (total_words + chunk_size - 1) // chunk_size
    
    print(f"\n{input_file.name}:")
    print(f"  Total: {total_words} words")
    print(f"  Chunks: {total_chunks} files")
    
    for i in range(total_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_words)
        chunk_words = words[start_idx:end_idx]
        
        output_file = DATA_DIR / f"{prefix}_part{i+1:02d}.csv"
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['word', 'translation'])
            for word_data in chunk_words:
                writer.writerow([word_data['word'], ''])
        
        print(f"  ✓ {output_file.name} ({len(chunk_words)} words)")

# Split MEDIUM
medium_file = DATA_DIR / "to_translate_2_MEDIUM.csv"
if medium_file.exists():
    split_file(medium_file, "translate_MEDIUM", 1000)

# Split HARD
hard_file = DATA_DIR / "to_translate_3_HARD.csv"
if hard_file.exists():
    split_file(hard_file, "translate_HARD", 1000)

print(f"\n✅ Done! Files created in: {DATA_DIR}")
print(f"\n📝 Translate each file and run:")
print(f"   python merge_all_translations.py")
