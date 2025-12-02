import collections
import csv
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import re
from concurrent.futures import ThreadPoolExecutor
import nltk
from nltk.tokenize import sent_tokenize

# BASE DIRECTORY
BASE_DIR = r"D:\infosys_project"

# 2. Text Extraction
file_path = rf"{BASE_DIR}\Bhagavad_geetha.txt"
print("\nExtracting text from text file...")
text = ''
with open(file_path, 'r', encoding='utf-8') as file:
    text = file.read()
print("✅ Text extraction complete.")
print("Total text length:", len(text))

# 3. Text Chunking
def chunk_text(text):
    paragraphs = text.split('\n\n')
    chunks = [p.strip() for p in paragraphs if p.strip()]
    return chunks

chunks = chunk_text(text)
print(f"\n✅ Total chunks created: {len(chunks)}")

# 4. Export Chunk Info to CSV
output_chunk_info_path = rf"{BASE_DIR}\chunk_info.csv"
with open(output_chunk_info_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['chunk_id', 'length', 'preview'])
    for i, chunk in enumerate(chunks):
        writer.writerow([i, len(chunk), chunk])
print(f"✅ Saved chunk info successfully at: {output_chunk_info_path}")

# 5. Create and Populate SQLite Database
db_path_chunks = rf"{BASE_DIR}\text_chunks.db"
conn_chunks = sqlite3.connect(db_path_chunks)
c_chunks = conn_chunks.cursor()
c_chunks.execute('''
    CREATE TABLE IF NOT EXISTS text_chunks (
        chunk_id INTEGER PRIMARY KEY,
        length INTEGER,
        chunk_content TEXT
    )
''')
conn_chunks.commit()

data_to_insert_chunks = [(i, len(chunk), chunk) for i, chunk in enumerate(chunks)]
c_chunks.executemany("INSERT INTO text_chunks (chunk_id, length, chunk_content) VALUES (?, ?, ?)", data_to_insert_chunks)
conn_chunks.commit()
conn_chunks.close()
print(f"✅ SQLite database created at: {db_path_chunks}")

# 6. Retrieve Chunks from DB
conn_chunks = sqlite3.connect(db_path_chunks)
c_chunks = conn_chunks.cursor()
c_chunks.execute("SELECT chunk_content FROM text_chunks")
rows = c_chunks.fetchall()
retrieved_chunks = [row[0] for row in rows]
conn_chunks.close()
print(f"✅ Retrieved {len(retrieved_chunks)} chunks from DB.")

# 7. Word Counting Function
def count_words_in_chunk(chunk_content):
    search_pattern = r"\b(karma|dharma|yoga|soul|self|life|death|truth|mind|god|spirit|action|desire|peace|knowledge|wisdom|faith|path|heart|body|rebirth)\b"
    target_words = [
        'karma', 'dharma', 'yoga', 'soul', 'self', 'life', 'death',
        'truth', 'mind', 'god', 'spirit', 'action', 'desire', 'peace',
        'knowledge', 'wisdom', 'faith', 'path', 'heart', 'body', 'rebirth'
    ]
    chunk_word_counts = {word: 0 for word in target_words}
    found_words = re.findall(search_pattern, chunk_content, re.IGNORECASE)
    for word in found_words:
        normalized_word = word.lower()
        if normalized_word in chunk_word_counts:
            chunk_word_counts[normalized_word] += 1
    return chunk_word_counts

print("✅ Function 'count_words_in_chunk' defined.")

# 8. Parallel Word Counting
total_aggregated_counts = collections.defaultdict(int)
with ThreadPoolExecutor(max_workers=8) as executor:
    chunk_results = executor.map(count_words_in_chunk, retrieved_chunks)
    for chunk_word_counts in chunk_results:
        for word, count in chunk_word_counts.items():
            total_aggregated_counts[word] += count
print(f"✅ Aggregated word counts using parallel processing.")

# 9. Save Word Counts to CSV
sorted_parallel_word_counts = sorted(total_aggregated_counts.items(), key=lambda item: item[1], reverse=True)
output_sorted_csv_path = rf"{BASE_DIR}\parallel_sorted_word_counts.csv"

with open(output_sorted_csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Word', 'Count'])
    for word, count in sorted_parallel_word_counts:
        writer.writerow([word, count])
print(f"✅ Word counts saved to: {output_sorted_csv_path}")

print("\nTotal Word Counts:")
for word, count in sorted_parallel_word_counts:
    print(f"{word.capitalize()}: {count}")

# 10. Create result DB
db_path_result = rf"{BASE_DIR}\result.db"
conn_result = sqlite3.connect(db_path_result)
c_result = conn_result.cursor()
c_result.execute('''
    CREATE TABLE IF NOT EXISTS word_counts (
        word TEXT PRIMARY KEY,
        count INTEGER
    )
''')
conn_result.commit()

c_result.execute("DELETE FROM word_counts")
data_to_insert_result = [(word, count) for word, count in sorted_parallel_word_counts]
c_result.executemany("INSERT INTO word_counts (word, count) VALUES (?, ?)", data_to_insert_result)
conn_result.commit()
conn_result.close()
print(f"✅ Word counts stored inside: {db_path_result}")

# 11. Visualization
n_words = 10
plot_data = sorted_parallel_word_counts[:n_words]
words = [item[0].capitalize() for item in plot_data]
counts = [item[1] for item in plot_data]

plt.figure(figsize=(12, 7))
sns.barplot(x=words, y=counts)
plt.title(f'Top {n_words} Most Frequent Words', fontsize=16)
plt.xlabel('Word')
plt.ylabel('Count')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
print("✅ Bar plot generated.")

# 12. Sentence Tokenization
all_sentences = []
for chunk_content in retrieved_chunks:
    all_sentences.extend(sent_tokenize(chunk_content))
print(f"\n✅ Total sentences: {len(all_sentences)}")

# 13. Rules
RULES = [
    {
        "rule_name": "karma_detector",
        "purpose": "Find sentences about duty, action, or karma.",
        "logic": r"\b(karma|action|duty|work|service)\b"
    },
    {
        "rule_name": "dharma_detector",
        "purpose": "Detect references to righteousness.",
        "logic": r"\b(dharma|righteousness|virtue|moral)\b"
    },
    {
        "rule_name": "yoga_detector",
        "purpose": "Identify meditation/yoga sentences.",
        "logic": r"\b(yoga|meditation|discipline|sadhana|union)\b"
    },
    {
        "rule_name": "soul_detector",
        "purpose": "Detect references to the soul.",
        "logic": r"\b(soul|self|atman|spirit|consciousness)\b"
    }
]
print("✅ Rules defined.")

# 14. Categorize Sentences

def extract_and_categorize_sentence(sentence, rules):
    for rule in rules:
        if re.search(rule['logic'], sentence, re.IGNORECASE):
            return rule['rule_name'], sentence
    return None

categorized_sentences = collections.defaultdict(list)

# --- Parallel execution without lambda ---
def process_sentence(sentence):
    return extract_and_categorize_sentence(sentence, RULES)

with ThreadPoolExecutor(max_workers=8) as executor:
    results = executor.map(process_sentence, all_sentences)

# Aggregate results
for result in results:
    if result:
        rule_name, matched_sentence = result
        categorized_sentences[rule_name].append(matched_sentence)

print("\n✅ Categorization Results (Parallel, No Lambda):")
for rule_name, sentences in categorized_sentences.items():
    print(f"{rule_name}: {len(sentences)}")

# 15. Pie Chart
rule_counts = {rule_name: len(sentences) for rule_name, sentences in categorized_sentences.items()}
labels = [rule.replace('_detector', '').capitalize() for rule in rule_counts]
sizes = list(rule_counts.values())

plt.figure(figsize=(10, 8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%')
plt.title("Sentence Distribution by Theme")
plt.show()
print("✅ Pie chart generated.")

