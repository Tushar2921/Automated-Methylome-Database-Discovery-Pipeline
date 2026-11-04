# Automated Methylome Database Discovery Pipeline

An automated Python pipeline for discovering novel methylome, WGBS, and RRBS databases from recent scientific literature. This workflow systematically mines citing publications to identify newly published epigenomic resources, filtering out noise to produce a high-quality candidate list for manual curation.

 Pipeline Overview

The pipeline consists of four sequential modules:

# 1. Citation Analysis (`1_citation_analysis.py`)
Queries the OpenAlex and Crossref APIs using parent database publications. It identifies all papers that have cited these databases within the last three years, calculates both lifetime and recent citation counts, and generates a master list of citing publications along with a citation summary.

# 2. Full-Text Harvesting (`2_fulltext_harvesting.py`)
Using the citing papers identified in Step 1, this script attempts to retrieve the full text through Europe PMC, Unpaywall, and publisher sources. When full text is unavailable, it retrieves the abstract via OpenAlex. Each paper is classified as:
# Fully Read
# Abstract Only
# Failed** (Paywalled/Unavailable)

# 3. Candidate Extraction (`3_extract_candidates.py`)
Analyzes the retrieved text using context-gated filtering. It processes only sentences containing both methylome-related keywords (e.g., WGBS, RRBS, bisulfite) and database-related terms (e.g., repository, atlas, portal). Strict regular expression patterns are then applied to extract potential database names.

# 4. Final Methylome Screening (`4_final_methylome_screening.py`)
Refines the extracted candidates by isolating the core proper noun representing each database. It applies multiple filtering strategies, including:
* An extensive blacklist to remove sequencing platforms (e.g., Illumina), software tools (e.g., Bismark), general repositories (e.g., GEO, TCGA), and generic biological terms.
* Fuzzy matching (`rapidfuzz`) to prevent the rediscovery of parent databases already included in the reference set.

# Note on the Final Output:
> Because the final screening module employs multiple layers of stringent filtering to eliminate irrelevant candidates, automated text mining can still produce a small number of false positives due to the complex nature of scientific text. Therefore, the final candidate list requires manual verification to confirm that the remaining entries represent genuine, novel methylome databases.

# Requirements

To run this pipeline, install the required Python packages:
```bash
pip install pandas requests beautifulsoup4 rapidfuzz openpyxl
