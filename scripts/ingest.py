import json
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.config import Settings
import chromadb

PARSED_DIR=Path("data/parsed")
CHROMA_DIR=Path("chromadb")
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE=512
CHUNK_OVERLAP=128
EMBEDDING_MODEL= "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME="medrag_v1"
def load_papers():
    papers=[]
    for filepath in PARSED_DIR.glob("*.json"):
        try:
            paper=json.loads(filepath.read_text())
            papers.append(paper)
        except Exception as e:
            print(f"Error loading {filepath.name}: {e}")
    print(f"Loaded {len(papers)} papers")
    return papers

def chunk_papers(papers):
    splitter=RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE,
     chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n","\n","."," "])
    all_chunks=[]
    all_metadata=[]
    for paper in papers:
        if not paper.get("body_text"):
            continue
        chunks=splitter.split_text(paper["body_text"])
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
            "pmc_id": paper.get("pmc_id", ""),
                "title": paper.get("title", ""),
                "journal": paper.get("journal", ""),
                "year": paper.get("year", ""),
                "chunk_index": i,
                "total_chunks": len(chunks),
             })
    print(f"Created {len(all_chunks)} chunks from {len(papers)} papers")
    return all_chunks, all_metadata

def embed_and_store(chunks,metadata):
    print(f"Loading embedding model {EMBEDDING_MODEL}")
    embeddings=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL,
    model_kwargs={"device":"cpu"})
    client=chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False)#this settings can also just be added in the .env file
    )
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection=client.create_collection(name=COLLECTION_NAME,metadata={"hnsw:space":"cosine"})
    batch_size=100
    for i in range(0,len(chunks),batch_size):
        batch_chunk=chunks[i:i+batch_size]
        batch_metadata=metadata[i:i+batch_size]
        batch_ids=[f"chunk_{j}" for j in range(i,i+len(batch_chunk))]
        batch_embeddings=embeddings.embed_documents(batch_chunk)
        collection.add(
            ids=batch_ids,
            documents=batch_chunk,
            embeddings=batch_embeddings,
            metadatas=batch_metadata
        )
def main():
    print("Starting ingestion pipeline...")
    print("=" * 50)

    papers = load_papers()
    chunks, metadata = chunk_papers(papers)
    embed_and_store(chunks, metadata)

    print("=" * 50)
    print("Ingestion complete!")
if __name__=="__main__":
    main()

\
# How many chunks are stored
#run in terminal
"""python -c "
import chromadb
client = chromadb.PersistentClient(path='./chromadb')
collection = client.get_collection('medrag_v1')
print(f'Total chunks in ChromaDB: {collection.count()}')
"

# How much disk space ChromaDB is using
du -sh chromadb/"""