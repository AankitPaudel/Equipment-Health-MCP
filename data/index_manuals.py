import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.utils import embedding_functions


def index_manuals():
    manuals_dir = os.path.join(os.path.dirname(__file__), "manuals")

    if not os.path.exists(manuals_dir):
        print("No manuals directory found")
        return

    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    ef = embedding_functions.DefaultEmbeddingFunction()

    try:
        chroma_client.delete_collection("equipment_manuals")
        print("Cleared existing collection")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name="equipment_manuals",
        embedding_function=ef
    )

    documents = []
    metadatas = []
    ids = []
    doc_id = 0

    for filename in sorted(os.listdir(manuals_dir)):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(manuals_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Split manuals into small chunks so retrieval can return focused context.
        chunk_size = 500
        words = content.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            if current_length >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        for chunk in chunks:
            documents.append(chunk)
            metadatas.append({"source": filename})
            ids.append(f"doc_{doc_id}")
            doc_id += 1

        print(f"Indexed {filename} - {len(chunks)} chunks")

    if not documents:
        print("No manual text files found")
        return

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"Done - {len(documents)} total chunks indexed into ChromaDB")


if __name__ == "__main__":
    index_manuals()