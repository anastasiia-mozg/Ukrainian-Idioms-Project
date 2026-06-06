# Ukrainian Idiom Extractor

A web application for automatic extraction of Ukrainian idioms from a text, combining two complementary approaches: dictionary-based search and a large language model.

---

## What it does

Given any Ukrainian text, the app splits it into sentences and runs two independent extraction pipelines in parallel:

- **Dictionary method** — matches sentences against a curated list of idioms taken from this (repo)[https://github.com/bohdana-ivakhnenko/ukrainian-idioms]. Before matching, both the input text and the dictionary entries are lemmatized using a Ukrainian spaCy model, which allows the system to catch inflected and morphologically varied forms of each idiom.
- **Model method (Gemini)** — sends the sentences to Google's Gemini 2.5 Flash Lite, which identifies idioms based on semantic and contextual understanding, without relying on any fixed vocabulary.

Results from both methods are displayed side by side, along with the idioms found by both — giving a sense of agreement between the two approaches.

---

## Features

- Processes arbitrary Ukrainian text of any length
- Detects idioms in inflected and morphologically varied forms
- Compares dictionary and LLM results with overlap detection
- Interactive bar chart showing idiom counts per method
- Downloadable CSV exports for both result sets
- Clean Streamlit UI (intro → input → results)

---

## Setup

**1. Clone the repository**

```bash
git clone <repo-url>
cd Ukrainian-Idioms-Project
```

**2. Install dependencies**

```bash
pip install -r code/requirements.txt
```

**3. Download the Ukrainian spaCy model**

```bash
python -m spacy download uk_core_news_lg
```

**4. Add your Google API key**

Create a file called `secrets.env` in the project root (this file is gitignored):

```
GOOGLE_API_KEY=your_key_here
```

**5. Run the app**

```bash
streamlit run code/main.py
```

---

## How the dictionary was built

The `VocabExtractor` class handles preprocessing of the raw idiom data. Starting from a TSV file with idiom entries and citations, it:

1. Parses bracket notation to generate surface form variants — e.g. `[не]` produces both forms with and without the word, and `word(synonym)` expands into multiple options
2. Generates additional variants by permuting word order and substituting interchangeable conjunctions and prepositions (`і/й/та`, `у/в`)
3. Lemmatizes all variants using spaCy so they can be matched against lemmatized input at runtime

The result is stored in `dicts/idiom_variants_dict.json`.

---

## Authors

Developed by **Анастасія Мозгова** and **Юліана Карпцова**, 2026.
