# Methylome Database Discovery Pipeline

Automated Python pipeline for discovering candidate **methylome**, **WGBS**, and **RRBS** databases from recent scientific literature.

This workflow starts from a list of known/parent methylome databases, identifies recent papers citing those databases, retrieves available full text or abstracts, extracts possible new database names, and performs strict final screening to generate a candidate list for manual review.

---

## Pipeline Overview

The pipeline contains four sequential Python scripts:

| Step | Script | Purpose |
|---|---|---|
| 1 | `1_citation_analysis.py` | Finds recent papers citing parent database publications using OpenAlex and Crossref |
| 2 | `2_fulltext_harversting.py` | Retrieves full text from PMC, Unpaywall, publisher pages, or abstracts from OpenAlex |
| 3 | `3_extract_candidates.py` | Extracts possible database names using methylome/database context filtering and regex |
| 4 | `4_final_methylome_screening.py` | Performs final filtering to remove tools, platforms, general repositories, parent databases, and false positives |

> **Important:** The final output is a candidate list, not a fully verified database list. Manual verification is required.

---

## Repository Files

Current scripts:

```text
1_citation_analysis.py
2_fulltext_harversting.py
3_extract_candidates.py
4_final_methylome_screening.py
```

> Note: The filename `2.2_fulltext_harversting.py` contains a spelling typo. The commands below use the exact uploaded filename. If you rename it later, update the run command accordingly.

---

## Requirements

### Python

Recommended:

```text
Python 3.9 or above
```

### Required Python Packages

Install dependencies using:

```bash
pip install -r requirements.txt
```

Required packages:

```text
pandas
requests
beautifulsoup4
openpyxl
rapidfuzz
```

---

## Input File Required

Before running the pipeline, create a file named:

```text
parent_databases.csv
```

This file must be placed in the same folder as the scripts.

### Required columns

```text
database_name,doi
```

### Example format

```csv
database_name,doi
MethBank,10.xxxx/example_doi_1
DiseaseMeth,10.xxxx/example_doi_2
MethHC,10.xxxx/example_doi_3
```

Replace the example DOIs with the actual publication DOIs of the parent databases.

### Column description

| Column | Description |
|---|---|
| `database_name` | Name of the known/parent methylome database |
| `doi` | DOI of the publication describing that database |

---

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
cd YOUR_REPOSITORY_NAME
```

### 2. Create a virtual environment

For Linux/Mac:

```bash
python -m venv .venv
source .venv/bin/activate
```

For Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install required packages

```bash
pip install -r requirements.txt
```

### 4. Add the input file

Make sure this file is present in the repository folder:

```text
parent_databases.csv
```

---

## How to Run the Pipeline

Run the scripts in the exact order below.

---

### Step 1: Citation Analysis

```bash
python 1_citation_analysis.py
```

### Input

```text
parent_databases.csv
```

### Output

```text
citation_summary.csv
citation_summary.xlsx
citing_papers.csv
citing_papers.xlsx
```

### What this step does

- Queries OpenAlex using the DOI of each parent database publication
- Retrieves citation counts from OpenAlex and Crossref
- Identifies citing papers from the last three years
- Generates a master list of citing publications

---

### Step 2: Full-Text Harvesting

```bash
python 2_fulltext_harversting.py
```

### Input

```text
citing_papers.csv
```

### Output

```text
paper_texts.csv
paper_texts.xlsx
failed_papers.csv
failed_papers.xlsx
```

### What this step does

For each citing paper, the script attempts to retrieve content from:

1. Europe PMC / PMC HTML
2. Unpaywall open-access links
3. Publisher HTML pages
4. OpenAlex abstract fallback

Each paper is classified as:

| Status | Meaning |
|---|---|
| `Fully Read` | Full text was retrieved |
| `Abstract Only` | Only abstract was available |
| `Failed` | Full text and abstract were unavailable or inaccessible |

---

### Step 3: Candidate Extraction

```bash
python 3_extract_candidates.py
```

### Input

```text
paper_texts.csv
parent_databases.csv
```

### Output

```text
new_database_mentions_cleaned.csv
new_database_mentions_cleaned.xlsx
```

### What this step does

- Uses only papers marked as `Fully Read` or `Abstract Only`
- Checks sentence context for methylome-related terms such as:

```text
methylome, WGBS, RRBS, bisulfite, DNA methylation, CpG
```

- Also requires database-related terms such as:

```text
database, repository, atlas, portal, archive, browser, platform
```

- Extracts possible database names using strict regular expressions
- Removes obvious irrelevant terms using blacklist filters

---

### Step 4: Final Methylome Screening

```bash
python 4_final_methylome_screening.py
```

### Input

```text
new_database_mentions_cleaned.xlsx
parent_databases.csv
```

### Output

```text
final_new_databases.csv
final_new_databases.xlsx
```

### What this step does

- Extracts the core database name from raw candidate mentions
- Removes known tools, sequencing platforms, file formats, general repositories, and generic biological terms
- Uses fuzzy matching to avoid rediscovering parent databases
- Produces a final candidate list for manual verification

---

## Final Output Format

The final output file contains:

```text
final_new_databases.csv
final_new_databases.xlsx
```

Expected columns:

| Column | Description |
|---|---|
| `Parent_Database` | Original database used to find citing papers |
| `Parent_DOI` | DOI of the parent database publication |
| `Citing_Paper_DOI` | DOI of the paper where the candidate was mentioned |
| `Citing_Paper_Title` | Title of the citing paper |
| `Citing_Paper_Year` | Publication year of the citing paper |
| `New_Database_Name` | Candidate database name extracted by the pipeline |

---

## Important Setup Notes

Before running the pipeline, make sure the scripts are valid Python files.

### 1. Section headings must be comments

Lines like this are not valid Python:

```python
=========================================
1. LOAD DATA
=========================================
```

They should be written as comments:

```python
# =========================================
# 1. LOAD DATA
# =========================================
```

### 2. Input/output filenames must match

Step 3 generates:

```text
new_database_mentions_cleaned.xlsx
```

Therefore, Step 4 should read:

```python
df = pd.read_excel("new_database_mentions_cleaned.xlsx")
```

If Step 4 uses:

```python
df = pd.read_excel("new_database_mentions.xlsx")
```

then either rename the file or update the code.

### 3. Unpaywall API email

Unpaywall requests usually require an email parameter. If needed, update the Unpaywall URL in Step 2 as:

```python
url = f"https://api.unpaywall.org/v2/{doi}?email=your_email@example.com"
```

Replace `your_email@example.com` with your actual email.

### 4. Internet connection is required

This pipeline uses external APIs and web sources:

- OpenAlex
- Crossref
- Europe PMC
- Unpaywall
- Publisher websites

API availability, rate limits, and paywall restrictions may affect the results.

---

## Recommended `.gitignore`

To avoid uploading large generated files, API outputs, or full-text article content, add a `.gitignore` file:

```text
.venv/
__pycache__/
*.pyc

citation_summary.csv
citation_summary.xlsx
citing_papers.csv
citing_papers.xlsx
paper_texts.csv
paper_texts.xlsx
failed_papers.csv
failed_papers.xlsx
new_database_mentions_cleaned.csv
new_database_mentions_cleaned.xlsx
final_new_databases.csv
final_new_databases.xlsx
```

You may keep a small anonymized/sample output file separately if you want to demonstrate the workflow.

---

## Limitations

This is an automated text-mining pipeline. Some false positives may remain because scientific papers often mention:

- Software tools
- Sequencing platforms
- General repositories
- Study names
- Biological concepts
- Previously known databases

Therefore, the final candidate list should be manually checked by visiting the database website, reading the source paper, and confirming that the candidate is truly a methylome/WGBS/RRBS-related database.

---

## Manual Verification Recommended

For each final candidate, verify:

1. Is it actually a database, atlas, portal, or repository?
2. Is it related to DNA methylation, methylome, WGBS, or RRBS data?
3. Is it different from the parent databases?
4. Does it have a working URL or accession/source?
5. Is it newly published or recently updated?
6. Is it not just a software tool, sequencing platform, or general repository?

---

## Summary

Run order:

```bash
python 1_citation_analysis.py
python 2.2_fulltext_harversting.py
python 3.1_extract_candidates.py
python 4_final_methylome_screening.py
```

Required starting file:

```text
parent_databases.csv
```

Final result:

```text
final_new_databases.xlsx
```

The final result is a curated candidate list for expert/manual validation.
