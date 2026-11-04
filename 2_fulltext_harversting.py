import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re

# =====================================================
# LOAD CITING PAPERS
# =====================================================
papers = pd.read_csv("citing_papers.csv")
rows = []

# =====================================================
# GENERATION TIMESTAMP
# =====================================================
generation_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# =====================================================
# GET PMC FULL TEXT HTML
# =====================================================
def get_pmc_html_text(pmcid):
    """Download and extract text from PMC HTML page"""
    try:
        url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        
        if r.status_code != 200:
            return ""
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Remove junk tags
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
            
        text = soup.get_text(separator=" ", strip=True)
        return text
    except Exception as e:
        return ""

# =====================================================
# GET UNPAYWALL OA LOCATION
# =====================================================
def get_unpaywall_oa(doi):
    """Use Unpaywall API to find OA version"""
    try:
        # Free Unpaywall API (no key needed for low usage)
        url = f"https://api.unpaywall.org/v2/{doi}"
        r = requests.get(url, timeout=20)
        
        if r.status_code != 200:
            return None, None
            
        data = r.json()
        
        if data.get("is_oa", False):
            best_oa = data.get("best_oa_location")
            if best_oa and best_oa.get("host_type") != "publisher":
                # Prefer repository versions over publisher
                return best_oa.get("url"), "repository"
            
            # Fall back to any OA location
            for loc in data.get("oa_locations", []):
                if loc.get("is_best", False):
                    return loc.get("url"), loc.get("host_type", "unknown")
                    
        return None, None
    except Exception:
        return None, None

# =====================================================
# SCRAPE PUBLISHER HTML
# =====================================================
def scrape_publisher_html(url, doi):
    """Try to scrape full text from publisher website"""
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        
        if r.status_code != 200:
            return ""
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Remove junk
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
            
        # Look for main content
        main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="article")
        
        if main_content:
            text = main_content.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)
            
        # Check if we got substantial content
        if len(text) > 3000:
            return text
            
        return ""
    except Exception:
        return ""

# =====================================================
# GET OPENALEX ABSTRACT (FALLBACK)
# =====================================================
def get_openalex_abstract(doi):
    """Get abstract from OpenAlex as fallback"""
    try:
        url = f"https://api.openalex.org/works/https://doi.org/{doi}"
        r = requests.get(url, timeout=20)
        
        if r.status_code != 200:
            return ""
            
        work = r.json()
        
        # Invert the abstract index
        inv_index = work.get("abstract_inverted_index", {})
        if not inv_index:
            return ""
            
        words = []
        for word, positions in inv_index.items():
            for pos in positions:
                words.append((pos, word))
        words.sort()
        
        return " ".join(word for _, word in words)
    except Exception:
        return ""

# =====================================================
# CHECK IF PAPER IS PAYWALLED
# =====================================================
def check_paywall_status(doi, europe_pmc_data):
    """Determine why paper is not available"""
    if not europe_pmc_data:
        return "Not indexed in Europe PMC"
    
    article = europe_pmc_data[0]
    doc_type = article.get("documentType", "").upper()
    is_oa = article.get("isOpenAccess", "N").upper()
    pmcid = article.get("pmcid")
    
    if doc_type in ["BOOK", "BOOK_SERIES", "BOOK_CHAPTER"]:
        return "Book/Book Chapter"
    elif doc_type == "RETRACTED_PUBLICATION":
        return "Retracted"
    elif not pmcid and is_oa == "N":
        return "Paywalled/Subscription"
    elif not pmcid and is_oa == "Y":
        return "OA but not in PMC"
    else:
        return "Unknown reason"

# =====================================================
# MAIN LOOP
# =====================================================
print(f"Processing {len(papers)} papers...")
print("Checking multiple sources: Europe PMC, Unpaywall, Publisher sites\n")

for idx, row in papers.iterrows():
    doi = str(row["citing_paper_doi"])
    
    if doi == "nan" or doi.strip() == "":
        continue
        
    clean_doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
    
    if (idx + 1) % 10 == 0:
        print(f"[{idx+1}/{len(papers)}] {clean_doi}")
    
    text = ""
    status = "Unknown"
    source = "none"
    
    try:
        # =====================================
        # STEP 1: Try Europe PMC
        # =====================================
        search_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{clean_doi}&format=json"
        r = requests.get(search_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        
        europe_pmc_data = None
        if r.status_code == 200:
            data = r.json()
            results = data.get("resultList", {}).get("result", [])
            if results:
                europe_pmc_data = results
                article = results[0]
                pmcid = article.get("pmcid")
                
                if pmcid:
                    full_text = get_pmc_html_text(pmcid)
                    if len(full_text) > 2000:
                        text = full_text
                        status = "Fully Read"
                        source = "PMC_HTML"
        
        # =====================================
        # STEP 2: Try Unpaywall (if Europe PMC failed)
        # =====================================
        if status != "Fully Read":
            oa_url, host_type = get_unpaywall_oa(clean_doi)
            
            if oa_url:
                full_text = scrape_publisher_html(oa_url, clean_doi)
                if len(full_text) > 2000:
                    text = full_text
                    status = "Fully Read"
                    source = f"Unpaywall_{host_type}"
        
        # =====================================
        # STEP 3: Try direct DOI resolver
        # =====================================
        if status != "Fully Read":
            doi_url = f"https://doi.org/{clean_doi}"
            full_text = scrape_publisher_html(doi_url, clean_doi)
            if len(full_text) > 2000:
                text = full_text
                status = "Fully Read"
                source = "Publisher_Direct"
        
        # =====================================
        # STEP 4: Fallback to abstract
        # =====================================
        if status != "Fully Read":
            abstract = get_openalex_abstract(clean_doi)
            if abstract and len(abstract) > 100:
                text = abstract
                status = "Abstract Only"
                source = "OpenAlex_Abstract"
            else:
                # Determine why it failed
                if europe_pmc_data:
                    reason = check_paywall_status(clean_doi, europe_pmc_data)
                    status = f"Failed: {reason}"
                else:
                    status = "Failed: Not found in any source"
                source = "none"
                
    except Exception as e:
        status = f"Failed: API Error"
        source = "none"
    
    # Save result
    rows.append({
        "parent_database": row["parent_database"],
        "parent_doi": row["parent_doi"],
        "citing_paper_doi": clean_doi,
        "title": row["citing_paper_title"],
        "publication_year": row.get("publication_year", ""),
        "status": status,
        "source": source,
        "text": text
    })
    
    time.sleep(0.5)  # Rate limiting (be nice to APIs)

# =====================================================
# SAVE OUTPUTS
# =====================================================
df = pd.DataFrame(rows)
df["generated_timestamp"] = generation_timestamp

# =====================================
# Metadata
# =====================================
total_papers = len(df)
fully_read = len(df[df["status"] == "Fully Read"])
abstract_only = len(df[df["status"] == "Abstract Only"])
failed = len(df[df["status"].str.contains("Failed", na=False)])

metadata = pd.DataFrame({
    "Parameter": [
        "Generated On",
        "Total Papers",
        "Fully Read",
        "Abstract Only",
        "Failed/Unavailable"
    ],
    "Value": [
        generation_timestamp,
        total_papers,
        fully_read,
        abstract_only,
        failed
    ]
})

# =====================================
# Save paper_texts
# =====================================
df.to_csv("paper_texts.csv", index=False)

with pd.ExcelWriter("paper_texts.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Paper Texts", index=False)
    metadata.to_excel(writer, sheet_name="Metadata", index=False)

# =====================================
# Save failed papers separately
# =====================================
failed_df = df[df["status"].str.contains("Failed", na=False)].copy()
failed_df.to_csv("failed_papers.csv", index=False)

with pd.ExcelWriter("failed_papers.xlsx", engine="openpyxl") as writer:
    failed_df.to_excel(writer, sheet_name="Failed Papers", index=False)
    metadata.to_excel(writer, sheet_name="Metadata", index=False)

# =====================================
# TERMINAL SUMMARY
# =====================================
print("\n==============================")
print("FULLY READ        :", fully_read)
print("ABSTRACT ONLY     :", abstract_only)
print("FAILED/UNAVAILABLE:", failed)
print("TOTAL PAPERS      :", total_papers)
print("==============================")
print("\nSource breakdown:")
print(df["source"].value_counts())
print("\nStatus breakdown:")
print(df["status"].value_counts())
print("\n================================")
print("Finished")
print("Generated on:", generation_timestamp)
print("================================")
print("\nCreated:")
print(" - paper_texts.csv")
print(" - paper_texts.xlsx")
print(" - failed_papers.csv")
print(" - failed_papers.xlsx")