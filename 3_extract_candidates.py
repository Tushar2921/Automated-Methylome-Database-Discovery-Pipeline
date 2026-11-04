import pandas as pd
import re

# =========================================
# 1. LOAD DATA
# =========================================
papers = pd.read_csv("paper_texts.csv")
papers = papers[papers["status"].isin(["Fully Read", "Abstract Only"])].copy()
parents = pd.read_csv("parent_databases.csv")
parent_dbs_lower = set(parents["database_name"].dropna().str.lower().tolist())

# =========================================
# 2. CONTEXT KEYWORDS
# =========================================
METHYLOME_CONTEXT = {
    "methylome", "wgbs", "rrbs", "whole genome bisulfite sequencing",
    "reduced representation bisulfite sequencing", "bisulfite sequencing",
    "bs-seq", "dna methylation", "5-methylcytosine", "5mc", "cpg island",
    "cpg site", "cpg shore", "dmr", "differentially methylated regions",
    "epigenome", "epigenomic", "methylation array", "bisulfite-seq"
}

DATABASE_KEYWORDS = {"database", "databases", "resource", "resources", "repository", 
                     "repositories", "atlas", "portal", "portals", "archive", "archives",
                     "browser", "knowledgebase", "platform", "collection", "hub"}

# =========================================
# 3. STRICT BLACKLISTS (The Garbage Filters)
# =========================================
# Common English words, verbs, prepositions, and Methods-section terms
STOPWORDS_BLACKLIST = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", 
    "by", "from", "via", "using", "as", "is", "are", "was", "were", "be", "been", "have", 
    "has", "had", "do", "does", "did", "we", "our", "this", "that", "these", "those", "it", 
    "its", "my", "your", "table", "figure", "methods", "results", "key", "shared", "expanded", 
    "included", "obtained", "downloaded", "deposited", "available", "process", "analysis", 
    "tissues", "lines", "including", "within", "between", "into", "based", "assessed", 
    "determined", "reagent", "star", "nih", "genome", "genomics", "epigenomics", "epigenome", 
    "cancer", "tumor", "cell", "blood", "plasma", "serum", "expression", "transcriptomic", 
    "proteomic", "metabolomic", "bismark", "bsmap", "methylkit", "dss", "limma", "seurat", 
    "cellranger", "macs2", "bowtie", "bwa", "trimmomatic", "fastqc", "samtools", "bedtools",
    "promoter", "enhancer", "gene", "genes", "protein", "rna", "dna", "cpg", "methylation",
    "methylated", "unmethylated", "hypermethylated", "hypomethylated", "study", "studies",
    "cohort", "cohorts", "patients", "samples", "data", "dataset", "datasets", "profile",
    "profiles", "signature", "signatures", "marker", "markers", "biomarker", "biomarkers",
    "viral", "genomic", "clinical", "public", "online", "web-based", "integrated", 
    "comprehensive", "novel", "new", "primary", "secondary", "advanced", "high-throughput"
}

# Known existing databases, tools, file formats, and sources. 
# Prevents extracting "GEO database", "UCSC browser", "WashU Epigenome", etc.
KNOWN_SOURCES_BLACKLIST = {
    "geo", "tcga", "ucsc", "washu", "ccle", "depmap", "ualcan", "gepia", "gepia2",
    "mexpress", "methsurv", "pride", "github", "sra", "encode", "ncbi", "ega", "ena", 
    "icgc", "pcawg", "cptac", "gtex", "fantom", "roadmap", "blueprint", "ihec", "cistrome",
    "jbrowse", "igv", "gdc", "xenahub", "xena", "cbioportal", "cbio", "string", "reactome",
    "kegg", "david", "enrichr", "gsea", "msigdb", "panther", "omim", "pubmed", "arxiv",
    "biorxiv", "medrxiv", "zenodo", "figshare", "dryad", "osf", "kaggle", "huggingface",
    "massarray", "bcntb", "methyldb", "methylbank", "diseasemeth", "methcancer", "mirdb",
    "targetscan", "fusiongdb", "lncexpdb", "tcod", "hall", "editome", "ewas", "bigsearch",
    "biocode", "openlb", "gwh", "gsa", "genbase", "bioproject", "biosample", "omix",
    "twas", "tedd", "cavddb", "metabolights", "metabolome", "peptide", "proteomicsdb",
    "arrayexpress", "ensembl", "uniprot", "pfam", "interpro", "vcf", "bed", "bam", "fastq",
    "gtf", "gff", "txt", "csv", "tsv", "xml", "json", "pdf", "html", "http", "https",
    "doi", "pmid", "pmcid", "orcid", "rrid", "issn", "isbn", "url", "uri", "ftp", "ssh"
}

def is_parent_db(name):
    name_clean = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
    for db in parent_dbs_lower:
        db_clean = re.sub(r'[^a-zA-Z0-9]', '', db)
        if name_clean == db_clean or name_clean in db_clean or db_clean in name_clean:
            return True
    return False

def is_valid_candidate(cand):
    """Strict validation to filter out garbage and existing tools"""
    cand_lower = cand.lower()
    
    # 1. Check against parent DBs
    if is_parent_db(cand):
        return False
        
    # 2. Check against known sources/tools/file formats
    if cand_lower in KNOWN_SOURCES_BLACKLIST:
        return False
        
    # 3. Check if ANY word in the candidate is a stopword/verb/preposition
    words = cand.split()
    if any(w.lower() in STOPWORDS_BLACKLIST for w in words):
        return False
        
    # 4. Length and character checks
    if len(cand) < 3 or len(cand) > 30:
        return False
        
    # 5. Must contain at least one uppercase letter (filters out pure lowercase noise)
    if not any(c.isupper() for c in cand):
        return False
        
    # 6. Should not be a single common dictionary word
    if len(words) == 1 and cand_lower in {"methylation", "epigenome", "methylome", "database", "portal", "atlas", "resource", "repository", "browser", "platform", "hub", "db"}:
        return False
        
    return True

def extract_candidates(text):
    candidates = set()
    
    # STRICT REGEX: NO re.IGNORECASE. 
    # Name must start with a capital letter, followed by alphanumeric/hyphens.
    NAME = r'\b([A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*){0,3})\b'
    KEYWORDS = r'(?:database|databases|resource|resources|repository|repositories|atlas|portal|portals|archive|archives|browser|knowledgebase|platform|collection|hub)'
    
    patterns = [
        rf'{NAME}\s+{KEYWORDS}',
        rf'{NAME}\s+is\s+(?:an?\s+)?(?:online\s+)?{KEYWORDS}',
        rf'\b(?:database|repository|atlas|portal)\s+(?:called|named|known as)\s+{NAME}',
        rf'{NAME}\s*\([^)]*\)\s+is\s+a\s+web-based\s+platform'
    ]
    
    for pattern in patterns:
        # NO re.IGNORECASE here! This is the silver bullet that stops "cancer DNA methylation biomarker"
        matches = re.findall(pattern, text)
        for match in matches:
            cand = match.strip()
            # Clean trailing punctuation
            cand = re.sub(r'[.,;:()\[\]]+$', '', cand)
            # Clean leading articles
            cand = re.sub(r'^(?:The|A|An|This|Our)\s+', '', cand)
            
            if is_valid_candidate(cand):
                candidates.add(cand)
                
    return candidates

# =========================================
# 4. MAIN EXTRACTION LOOP
# =========================================
rows = []
print(f"Extracting candidates from {len(papers)} papers...")

for idx, row in papers.iterrows():
    text = str(row["text"])
    if len(text) < 100:
        continue
        
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for i, sentence in enumerate(sentences):
        context = " ".join(sentences[max(0, i-1):min(len(sentences), i+2)])
        lower_ctx = context.lower()
        
        # Must have BOTH methylome context AND database words
        if not any(word in lower_ctx for word in DATABASE_KEYWORDS):
            continue
        if not any(word in lower_ctx for word in METHYLOME_CONTEXT):
            continue
            
        candidates = extract_candidates(context)
        
        for cand in candidates:
            rows.append({
                "parent_database": row["parent_database"],
                "parent_doi": row["parent_doi"],
                "citing_paper_doi": row["citing_paper_doi"],
                "paper_title": row["title"],
                "publication_year": row.get("publication_year", ""),
                "candidate_database": cand,
                "evidence": context[:800]
            })

# =========================================
# 5. SAVE OUTPUT
# =========================================
df_out = pd.DataFrame(rows)
df_out = df_out.drop_duplicates(subset=["candidate_database", "citing_paper_doi"])

df_out.to_csv("new_database_mentions_cleaned.csv", index=False)
df_out.to_excel("new_database_mentions_cleaned.xlsx", index=False)

print(f"\n✅ Extracted {len(df_out)} clean candidates. Garbage successfully filtered out.")
print("Saved to: new_database_mentions_cleaned.csv / .xlsx")