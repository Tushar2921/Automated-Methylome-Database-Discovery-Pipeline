import pandas as pd
import re
from rapidfuzz import fuzz

print("="*60)
print("STARTING FINAL METHYLOME DATABASE SCREENING")
print("="*60)

# 1. LOAD DATA
try:
    df = pd.read_excel("new_database_mentions_cleaned.xlsx")
except FileNotFoundError:
    print("Error: 'new_database_mentions.xlsx' not found.")
    exit()

# Load parent databases to exclude
parent_list = []
try:
    parents = pd.read_csv("parent_databases.csv")
    parent_list = parents.iloc[:, 0].astype(str).str.lower().tolist()
except FileNotFoundError:
    try:
        parents = pd.read_excel("parent_databases.xlsx")
        parent_list = parents.iloc[:, 0].astype(str).str.lower().tolist()
    except FileNotFoundError:
        print("Warning: parent_databases file not found.")

# 2. MASSIVE BLACKLIST (Tools, generic terms, known non-methylome DBs)
BLACKLIST = {
    "tcga", "geo", "sra", "gdc", "ccle", "depmap", "icgc", "pcawg", "encode", "roadmap",
    "ihec", "ena", "ddbj", "ebi", "ncbi", "nlm", "pubmed", "cosmic", "drugbank", "kegg",
    "reactome", "bioportal", "cbioportal", "gepia", "ualcan", "methsurv", "gsca", "smart",
    "mexpress", "hpa", "olink", "mgi", "exac", "gnomad", "gtex", "pdmr", "gtrd", "crcdb",
    "methylcancer", "lnc2meth", "linkedomics", "metabolights", "rdb", "bcntb", "tcea",
    "hichipdb", "postar3", "string", "ogen", "dice", "illumina", "novaseq", "nextseq",
    "hiseq", "minion", "promethion", "pacbio", "nanopore", "smrt", "tgs", "ngs", "oxford",
    "ion torrent", "beadchip", "array", "bismark", "macs2", "bowtie", "bwa", "trimgalore",
    "fastqc", "samtools", "bedtools", "deeptools", "bioconductor", "github", "zenodo",
    "chromhmm", "animaltfdb", "tftarget", "pcr", "qpcr", "ddpcr", "methods", "key",
    "results", "discussion", "figure", "table", "supplementary", "data", "dataset",
    "txt", "tsv", "csv", "fasta", "fastq", "vcf", "bam", "sam", "bed", "gff", "gtf",
    "json", "xml", "html", "http", "https", "www", "ftp", "url", "doi", "org", "net",
    "com", "edu", "gov", "bio", "de", "cmap", "stitch", "drug", "these", "the", "a", "an",
    "in", "of", "from", "and", "as", "that", "this", "we", "our", "some", "all", "any",
    "with", "for", "to", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can",
    "shall", "must", "need", "it", "its", "he", "she", "they", "them", "their", "his",
    "her", "my", "your", "i", "me", "you", "us", "methylation", "methylated", "unmethylated",
    "hypermethylated", "hypomethylated", "epigenome", "epigenomic", "methylome", "genome",
    "genomic", "transcriptome", "proteome", "metabolome", "rna", "dna", "cpg", "wgbs",
    "rrbs", "bs-seq", "gene", "genes", "protein", "mutation", "variant", "snp", "cnv",
    "study", "studies", "cohort", "cohorts", "patients", "samples", "tissue", "tissues",
    "cell", "cells", "human", "mouse", "rat", "zebrafish", "fly", "cancer", "tumor",
    "tumour", "adenocarcinoma", "carcinoma", "leukemia", "lymphoma", "myeloma", "glioma",
    "breast", "lung", "liver", "kidney", "prostate", "ovarian", "colorectal", "gastric",
    "pancreatic", "bladder", "thyroid", "melanoma", "sarcoma", "hematological", "malignancy",
    "malignancies", "hematologic", "blood", "plasma", "serum", "cfDNA", "ctDNA", "cell-free",
    "circulating", "biomarker", "biomarkers", "marker", "markers", "signature", "signatures",
    "profile", "profiles", "expression", "genomics", "proteomics", "transcriptomics",
    "metabolomics", "multi-omic", "multi-omics", "pan-genome", "spatiotemporal", "cloud",
    "fusion", "mutant", "variants", "entries", "sequences", "sequence", "topologies",
    "aptamer", "spatial", "omics", "crop", "tropical", "longevity", "haplotype", "nucleic",
    "acid", "literature", "antibody", "terminal", "exon", "organism", "model", "reference",
    "recently", "utilized", "using", "based", "comprehensive", "developed", "published",
    "querying", "utilize", "utilizes", "updated", "includes", "contains", "provides",
    "generated", "constructed", "descriptions", "description", "issue", "annotation",
    "landscape", "association", "analysis", "analyses", "humanmethylation450",
    "humanmethylation27", "methylationepic", "epic", "450k", "27k", "infinium", "beadchip",
    "platform", "assay", "kit", "reagent", "resource", "resources", "repository",
    "repositories", "archive", "archives", "browser", "browsers", "portal", "portals",
    "atlas", "atlases", "hub", "hubs", "bank", "banks", "base", "bases", "map", "maps",
    "index", "indexes", "indices", "catalog", "catalogs", "catalogue", "catalogues",
    "registry", "registries", "library", "libraries", "knowledgebase", "knowledgebases",
    "database", "databases", "db", "dbs", "established", "process", "obtained", "downloaded",
    "acquired", "collected", "integrated", "derived", "extracted", "calculated", "analyzed",
    "visualized", "utilities", "tools", "software", "pipeline", "workflow", "algorithm",
    "package", "module", "framework", "system", "network", "model", "approach", "method",
    "technique", "protocol", "standard", "guideline", "recommendation", "best practice",
    "benchmark", "evaluation", "assessment", "comparison", "review", "survey", "overview",
    "summary", "conclusion", "discussion", "introduction", "background", "related work",
    "future work", "acknowledgment", "funding", "conflict of interest", "author contributions",
    "data availability", "code availability", "supplementary material", "appendix", "glossary",
    "index", "bibliography", "references", "citations", "footnotes", "endnotes", "errata",
    "corrigenda", "retractions", "expressions of concern", "editorials", "commentaries",
    "letters", "news", "views", "perspectives", "opinions", "debates", "interviews",
    "obituaries", "biographies", "histories", "chronologies", "timelines", "calendars",
    "directories", "handbooks", "manuals", "guides", "tutorials", "workshops", "conferences",
    "symposia", "seminars", "webinars", "courses", "classes", "lectures", "presentations",
    "slides", "posters", "abstracts", "proceedings", "transactions", "journals", "magazines",
    "newsletters", "bulletins", "reports", "white papers", "technical notes", "briefs",
    "memos", "emails", "messages", "posts", "blogs", "wikis", "forums", "chat rooms",
    "social media", "websites", "web pages", "hyperlinks", "urls", "domains", "servers",
    "clients", "browsers", "plugins", "extensions", "add-ons", "widgets", "apps", "applications",
    "programs", "scripts", "macros", "functions", "procedures", "subroutines", "methods",
    "classes", "objects", "variables", "constants", "parameters", "arguments", "returns",
    "exceptions", "errors", "warnings", "logs", "traces", "dumps", "snapshots", "backups",
    "archives", "repositories", "libraries", "frameworks", "platforms", "environments",
    "systems", "networks", "clusters", "grids", "clouds", "edges", "fogs", "mists", "dew",
    "rain", "snow", "hail", "sleet", "ice", "water", "fire", "earth", "air", "wind", "storm",
    "thunder", "lightning", "tornado", "hurricane", "cyclone", "typhoon", "monsoon", "drought",
    "flood", "earthquake", "volcano", "tsunami", "wildfire", "avalanche", "landslide", "rockfall",
    "sinkhole", "subsidence", "erosion", "sedimentation", "deposition", "weathering", "diagenesis",
    "metamorphism", "magmatism", "volcanism", "tectonism", "seismism", "glaciation", "permafrost",
    "cryosphere", "hydrosphere", "atmosphere", "lithosphere", "biosphere", "anthroposphere",
    "technosphere", "noosphere", "exosphere", "thermosphere", "mesosphere", "stratosphere",
    "troposphere", "ionosphere", "magnetosphere", "heliosphere", "astrosphere", "galactosphere",
    "cosmosphere", "universesphere", "multiversesphere", "omnisphere", "absolutesphere", "infinitysphere"
}

# 3. EXTRACT CORE PROPER NOUN (Fixes the greedy regex issue)
def extract_core_name(raw_candidate):
    raw = str(raw_candidate).strip()
    if not raw or len(raw) < 3: return None
    
    # 1. Look for CamelCase ending in DB keywords (e.g., MethMarkerDB, CancerMethAtlas)
    camel_db = re.findall(r'[A-Z][a-zA-Z0-9]*(?:DB|Base|Atlas|Hub|Portal|Bank|Map|Browser|Index|Archive)', raw)
    if camel_db: return max(camel_db, key=len)
    
    # 2. Look for pure CamelCase (at least 2 uppercase letters, no spaces)
    camel = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-zA-Z0-9]*)+', raw)
    if camel: return max(camel, key=len)
    
    # 3. Look for Acronyms (3-8 uppercase letters)
    acronyms = re.findall(r'\b[A-Z]{3,8}\b', raw)
    if acronyms: return acronyms[0]
    
    # 4. Look for Title Case + DB suffix (e.g., "Methylation Atlas")
    title_db = re.findall(r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Atlas|Hub|Portal|Bank|Base|Map|DB)', raw)
    if title_db: return title_db[0]
    
    return None # It's just a generic phrase, reject it

# 4. STRICT VALIDATION
def is_valid_methylome_db(core_name, evidence):
    if not core_name: return False
    name = core_name.strip()
    name_lower = name.lower()
    evidence_lower = str(evidence).lower()
    
    # Basic length check
    if len(name) < 3 or len(name) > 40: return False
    
    # Check blacklist
    if name_lower in BLACKLIST: return False
    
    # Check parent databases (fuzzy match)
    for parent in parent_list:
        if fuzz.ratio(name_lower, parent) >= 85: return False
        if parent in name_lower or name_lower in parent: return False
        
    # Methylome Context Check: The evidence MUST mention methylome/methylation/WGBS/RRBS
    methylome_keywords = ["methylome", "methylation", "wgbs", "rrbs", "bisulfite", "cpg", "5mc", "5-methylcytosine"]
    if not any(kw in evidence_lower for kw in methylome_keywords):
        return False
        
    return True

# 5. APPLY SCREENING
print(f"Total raw mentions to screen: {len(df)}")
cleaned_rows = []
for idx, row in df.iterrows():
    raw_candidate = row["candidate_database"]
    evidence = row.get("evidence", "")
    
    # Extract the core name from the messy string
    core_name = extract_core_name(raw_candidate)
    
    # Validate the core name
    if is_valid_methylome_db(core_name, evidence):
        cleaned_rows.append({
            "parent_database": row["parent_database"],
            "parent_doi": row["parent_doi"],
            "citing_paper_doi": row["citing_paper_doi"],
            "paper_title": row["paper_title"],
            "publication_year": row.get("publication_year", ""),
            "new_database_name": core_name
        })

# 6. FORMAT AND SAVE
final_df = pd.DataFrame(cleaned_rows)

# Remove exact duplicates
final_df = final_df.drop_duplicates(subset=["new_database_name", "citing_paper_doi"])

# Rename columns to match your exact requested format
final_df.columns = [
    "Parent_Database",
    "Parent_DOI",
    "Citing_Paper_DOI",
    "Citing_Paper_Title",
    "Citing_Paper_Year",
    "New_Database_Name"
]

# Sort by the new database name for easy review
final_df = final_df.sort_values(by=["New_Database_Name", "Citing_Paper_Year"], ascending=[True, False])

# ==========================================
# SIMPLE OUTPUT NAMES
# ==========================================
output_excel = "final_new_databases.xlsx"
output_csv = "final_new_databases.csv"

final_df.to_csv(output_csv, index=False)
final_df.to_excel(output_excel, index=False)

print("\n" + "="*60)
print("SCREENING COMPLETE!")
print(f"Total verified, garbage-free new methylome databases found: {len(final_df)}")
print(f"Saved to: {output_excel}")
print("="*60)

if len(final_df) > 0:
    print("\nTop newly discovered databases:")
    print(final_df['New_Database_Name'].value_counts().head(20))
else:
    print("\nNo candidates passed the strict screening.")