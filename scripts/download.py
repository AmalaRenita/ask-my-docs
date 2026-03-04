import urllib.request
import gzip
import shutil
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

RAW_DIR=Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
PAPERS = [
    "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/oa_comm/xml/oa_comm_xml.incr.2024-01-01.tar.gz"
]
def get_download_urls():
    index_url = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/oa_comm/xml/"
    print(f"Checking PubmED ftp INDEX AT {index_url}")
    with urllib.request.urlopen(index_url) as response:
        html=response.read().decode("utf-8")
    urls=[]
    for line in html.splitlines():
        if "baseline" in line and ".tar.gz" in line:
            filename=line.split('"')[1]
            file_url=index_url+filename
            urls.append(file_url)
    return(urls)

def download_file(url:str, destination:Path)->None:
    print(f"(Downloading {url}....)")
    urllib.request.urlretrieve(url,destination)
    print(f"Saved to {destination}")

def extract_file(filepath:Path)->None:
    print(f"Extracting {filepath}....")
    extract_path=RAW_DIR/filepath.stem.replace(".tar","")
    extract_path.mkdir(exist_ok=True)
    shutil.unpack_archive(filepath,extract_path)
    print(f"Extracted to {extract_path}")
    filepath.unlink()
    print(f"Deleted archive {filepath}")

def main():
    urls=get_download_urls()
    if not urls:
        print("No files found — printing page for debugging:")
        return
    for url in urls[:2]:
        filename=url.split("/")[-1]
        destination=RAW_DIR/filename
        download_file(url,destination)
        extract_file(destination)

if __name__=="__main__":
    main()