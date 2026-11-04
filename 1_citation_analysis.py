import pandas as pd
import requests
import time
from datetime import datetime

# Settings
YEARS_BACK = 3
current_year = datetime.now().year
from_year = current_year - YEARS_BACK

# Load input CSV
df_parents = pd.read_csv("parent_databases.csv")

summary_rows = []
citing_papers_rows = []

def get_citations_crossref(doi):
    """Get citation count from Crossref"""
    try:
        url = f"https://api.crossref.org/works/{doi}"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return data.get("message", {}).get("is-referenced-by-count", 0)
    except:
        pass
    return 0

def get_citing_papers_openalex(openalex_id, from_year):
    """Get citing papers from OpenAlex with pagination"""
    papers = []
    cursor = "*"
    
    while True:
        query = (
            f"https://api.openalex.org/works"
            f"?filter=cites:{openalex_id},from_publication_date:{from_year}-01-01"
            f"&per-page=200&cursor={cursor}"
        )
        try:
            r = requests.get(query, timeout=60)
            if r.status_code != 200:
                break
                
            data = r.json()
            results = data.get("results", [])
            if not results:
                break
                
            papers.extend(results)
            
            next_cursor = data["meta"].get("next_cursor")
            if not next_cursor:
                break
            cursor = next_cursor
            time.sleep(0.5)
        except:
            break
    
    return papers

# Process each database
for idx, row in df_parents.iterrows():
    parent_name = row["database_name"]
    doi = str(row["doi"]).strip()
    
    print(f"Processing: {parent_name} ({doi})")
    
    total_citations_openalex = 0
    total_citations_crossref = 0
    count_3_years = 0
    openalex_id = None
    
    try:
        # Get data from OpenAlex
        url = f"https://api.openalex.org/works/https://doi.org/{doi}"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            work = r.json()
            openalex_id = work.get("id")
            total_citations_openalex = work.get("cited_by_count", 0)
        
        # Get data from Crossref
        total_citations_crossref = get_citations_crossref(doi)
        
        # Use the MAXIMUM of both sources for better accuracy
        total_citations = max(total_citations_openalex, total_citations_crossref)
        
        # Get citing papers from last 3 years
        if openalex_id:
            papers = get_citing_papers_openalex(openalex_id, from_year)
            count_3_years = len(papers)
            
            for paper in papers:
                citing_papers_rows.append({
                    "parent_database": parent_name,
                    "parent_doi": doi,
                    "citing_paper_doi": paper.get("doi"),
                    "citing_paper_title": paper.get("display_name"),
                    "publication_year": paper.get("publication_year")
                })
        
        print(f"  OpenAlex: {total_citations_openalex}, Crossref: {total_citations_crossref}, Max: {total_citations}, Last 3 yrs: {count_3_years}")
        
    except Exception as e:
        print(f"  Error: {e}")
        total_citations = 0
        
    summary_rows.append({
        "Database_Name": parent_name,
        "Verified_DOI": doi,
        "Total_Citations_GS": total_citations,
        "Citations_Last_3yrs": count_3_years
    })
    
    time.sleep(1)  # Be nice to the APIs

# Save outputs
df_summary = pd.DataFrame(summary_rows)
df_summary.to_csv("citation_summary.csv", index=False)
df_summary.to_excel("citation_summary.xlsx", index=False)

df_citing = pd.DataFrame(citing_papers_rows)
df_citing.to_csv("citing_papers.csv", index=False)
df_citing.to_excel("citing_papers.xlsx", index=False)

print("\nDone! Files saved:")
print(" - citation_summary.csv/xlsx")
print(" - citing_papers.csv/xlsx")