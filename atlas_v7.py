"""atlas_v7.py — RAG-enabled Atlas: document indexing, retrieval, and cited generation.

Indexes a local corpus into ChromaDB, retrieves relevant chunks via
embedding similarity, and generates answers with source citations.

Requires: ANTHROPIC_API_KEY and OPENAI_API_KEY environment variables.
Usage: python atlas_v7.py
"""

import os
import re
import time
import chromadb
from pathlib import Path
from openai import OpenAI
from anthropic import Anthropic

# ============================================================================
# Configuration
# ============================================================================

CORPUS_DIR = "./sample_corpus"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "atlas_codebase"

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".md", ".txt", ".json"}
MAX_FILE_SIZE = 100_000
EMBEDDING_MODEL = "text-embedding-3-small"

openai_client = OpenAI()
anthropic_client = Anthropic()


# ============================================================================
# Document Loading
# ============================================================================

def load_documents(corpus_dir: str) -> list[dict]:
    """Load text files from a directory with metadata."""
    docs = []
    corpus_path = Path(corpus_dir).resolve()
    for file_path in corpus_path.rglob("*"):
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Skipping {file_path}: {e}")
            continue
        if len(text) > MAX_FILE_SIZE:
            text = text[:MAX_FILE_SIZE]
        relative = file_path.relative_to(corpus_path)
        docs.append({"path": str(relative), "extension": file_path.suffix, "text": text})
    return docs


# ============================================================================
# Chunking
# ============================================================================

def chunk_text_fixed(text: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """Split text into fixed-size character chunks with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append({"text": text[start:end], "start_char": start})
        start = end - overlap
    return chunks


def estimate_line_range(text: str, start_char: int, chunk_length: int) -> tuple[int, int]:
    """Estimate start and end line numbers for a chunk."""
    start_line = text[:start_char].count("\n") + 1
    end_line = text[:start_char + chunk_length].count("\n") + 1
    return start_line, end_line


# ============================================================================
# Embeddings
# ============================================================================

def get_embedding(text: str, max_retries: int = 3) -> list[float]:
    """Get embedding from OpenAI with retry logic."""
    for attempt in range(max_retries):
        try:
            response = openai_client.embeddings.create(input=text, model=EMBEDDING_MODEL)
            return response.data[0].embedding
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts in one API call."""
    response = openai_client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in response.data]


# ============================================================================
# Indexing
# ============================================================================

def index_corpus(corpus_dir: str, collection) -> int:
    """Index a corpus directory into ChromaDB. Returns total chunk count."""
    docs = load_documents(corpus_dir)
    if not docs:
        print("No documents found.")
        return 0

    existing_ids = set(collection.get()["ids"]) if collection.count() > 0 else set()
    all_chunks, all_ids, all_metadatas = [], [], []

    for doc in docs:
        chunks = chunk_text_fixed(doc["text"])
        for i, chunk_info in enumerate(chunks):
            chunk_id = f"{doc['path']}_chunk_{i}"
            if chunk_id in existing_ids:
                continue
            chunk_text = chunk_info["text"]
            start_line, end_line = estimate_line_range(
                doc["text"], chunk_info["start_char"], len(chunk_text)
            )
            all_chunks.append(chunk_text)
            all_ids.append(chunk_id)
            all_metadatas.append({
                "file_path": doc["path"],
                "extension": doc["extension"],
                "chunk_index": i,
                "line_start": start_line,
                "line_end": end_line,
            })

    if not all_chunks:
        print("All chunks already indexed.")
        return collection.count()

    # Embed in batches of 100
    all_embeddings = []
    for batch_start in range(0, len(all_chunks), 100):
        batch = all_chunks[batch_start:batch_start + 100]
        all_embeddings.extend(get_embeddings_batch(batch))

    collection.add(
        ids=all_ids, documents=all_chunks,
        embeddings=all_embeddings, metadatas=all_metadatas,
    )
    print(f"Indexed {len(all_chunks)} new chunks from {len(docs)} files.")
    return collection.count()


# ============================================================================
# Retrieval
# ============================================================================

def retrieve_chunks(question: str, collection, n_results: int = 5) -> dict:
    """Retrieve top-k chunks by embedding similarity."""
    query_embedding = get_embedding(question)
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )


def print_retrieval_results(results: dict):
    """Print retrieved chunks for debugging."""
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        metadata = results["metadatas"][0][i]
        doc_preview = results["documents"][0][i][:120]
        line_info = f"lines {metadata.get('line_start', '?')}-{metadata.get('line_end', '?')}"
        print(f"\n  Result {i + 1} (distance: {distance:.4f})")
        print(f"  File: {metadata['file_path']}, chunk {metadata['chunk_index']}, {line_info}")
        print(f"  Preview: {doc_preview}...")


# ============================================================================
# Generation with Citations
# ============================================================================

def build_rag_prompt(question: str, results: dict) -> tuple[str, list[dict]]:
    """Build system prompt and messages for grounded generation."""
    context_blocks = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        text = results["documents"][0][i]
        line_info = f"lines {meta.get('line_start', '?')}-{meta.get('line_end', '?')}"
        context_blocks.append(
            f"[Source: {meta['file_path']}, chunk {meta['chunk_index']}, {line_info}]\n{text}"
        )
    context_str = "\n\n---\n\n".join(context_blocks)

    system_prompt = (
        "You are Atlas, a code assistant that answers questions using ONLY the "
        "retrieved source context below. Rules:\n"
        "1. Answer based solely on the provided context.\n"
        "2. Cite every claim with [filename, chunk N, lines X-Y].\n"
        "3. If the context is insufficient, say so.\n"
        "4. Do not use knowledge from outside the provided context."
    )
    messages = [{"role": "user", "content": f"## Retrieved Context\n\n{context_str}\n\n## Question\n\n{question}"}]
    return system_prompt, messages


# ============================================================================
# Main
# ============================================================================

def main():
    print("Atlas v7 — RAG-Enabled Code Assistant\n")

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    total = index_corpus(CORPUS_DIR, collection)
    print(f"Collection has {total} chunks.\n")

    while True:
        try:
            question = input("Ask Atlas: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not question or question.lower() in ("quit", "exit"):
            break

        results = retrieve_chunks(question, collection, n_results=5)
        print("\n--- Retrieved chunks ---")
        print_retrieval_results(results)

        system_prompt, messages = build_rag_prompt(question, results)
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-6", max_tokens=1024,
            system=system_prompt, messages=messages,
        )
        print(f"\n--- Atlas ---\n{message.content[0].text}\n")


if __name__ == "__main__":
    main()
