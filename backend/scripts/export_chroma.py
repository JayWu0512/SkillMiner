# backend/scripts/export_chroma.py
from pathlib import Path
import json
import chromadb
from chromadb.config import Settings

# Locate the chroma directory (relative to backend)
CHROMA_DIR = Path(__file__).resolve().parents[1] / "chroma"
EXPORT_FILE = Path(__file__).resolve().parents[1] / "chroma_export.jsonl"

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR),
    settings=Settings(anonymized_telemetry=False)
)

print(f"Exporting collections from {CHROMA_DIR} ...")

export = {}
for coll in client.list_collections():
    c = client.get_collection(coll.name)
    data = c.get(include=["embeddings", "documents", "metadatas", "uris"])
    export[coll.name] = data
    print(f"Exported collection: {coll.name} ({len(data['ids'])} entries)")

with open(EXPORT_FILE, "w") as f:
    for name, data in export.items():
        for i, _id in enumerate(data["ids"]):
            row = {
                "collection": name,
                "id": _id,
                "document": (data["documents"][i] if data.get("documents") else None),
                "metadata": (data["metadatas"][i] if data.get("metadatas") else None),
                "embedding": (data["embeddings"][i] if data.get("embeddings") else None),
                "uri": (data["uris"][i] if data.get("uris") else None),
            }
            f.write(json.dumps(row) + "\n")

print(f"\n✅ Done! Exported all collections to: {EXPORT_FILE}")
