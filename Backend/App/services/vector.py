import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("indusbrain")

# Dynamic ChromaDB import check
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

class VectorService:
    def __init__(self):
        self.client = None
        self.collection = None
        self.connected = False
        
        # Simple local in-memory store for fallback/demonstration
        self.mock_store = [
            {
                "id": "doc_pmp_1",
                "text": "SOP_FeedPump_v2.pdf: Pre-start checklist for Feed Pump PMP-101. Verify auxiliary lube oil pressure is above 1.8 bar. Open suction valve to 100% open. Keep discharge valve closed.",
                "metadata": {"source": "SOP_FeedPump_v2.pdf", "asset": "PMP-101", "type": "SOP"}
            },
            {
                "id": "doc_vlv_1",
                "text": "Valve_OEM_Guide_v3.pdf: OEM Technical guidelines for Pneumatic Control Valve VLV-204. Nominal input air pressure is 5.5 bar. High sticking risk if dry air filters are saturated with moisture.",
                "metadata": {"source": "Valve_OEM_Guide_v3.pdf", "asset": "VLV-204", "type": "OEM"}
            },
            {
                "id": "doc_blr_1",
                "text": "SOP_Boiler_v4.pdf: Standard Operating Procedures for high pressure Boiler BLR-302 block C. Steam temperature must not exceed 620 degrees C to avoid tube creep deformation.",
                "metadata": {"source": "SOP_Boiler_v4.pdf", "asset": "BLR-302", "type": "SOP"}
            },
            {
                "id": "doc_reg_1",
                "text": "OISD-STD-189 Section 6.2: Boilers safety relief valves testing and recalibration mandates. Certifications must occur every 12 months. Hydrostatic test is required prior to startup.",
                "metadata": {"source": "OISD-STD-189", "asset": "BLR-302", "type": "Regulation"}
            }
        ]

        if HAS_CHROMADB:
            try:
                # Persistent storage in local folder
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chroma_data")
                os.makedirs(db_path, exist_ok=True)
                self.client = chromadb.PersistentClient(path=db_path)
                self.collection = self.client.get_or_create_collection("industrial_corpus")
                self.connected = True
                
                # Seed collection if empty
                if self.collection.count() == 0:
                    self._seed_collection()
                logger.info("Initialized ChromaDB vector database collection.")
            except Exception as e:
                logger.warning(f"ChromaDB initialization failed: {e}. Falling back to in-memory store.")

    def _seed_collection(self):
        ids = [doc["id"] for doc in self.mock_store]
        documents = [doc["text"] for doc in self.mock_store]
        metadatas = [doc["metadata"] for doc in self.mock_store]
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """
        Add a document chunk to the vector database.
        """
        if self.connected and self.collection:
            self.collection.add(ids=[doc_id], documents=[text], metadatas=[metadata])
        else:
            self.mock_store.append({
                "id": doc_id,
                "text": text,
                "metadata": metadata
            })

    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Perform semantic search against indexed document chunks.
        """
        if self.connected and self.collection:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                
                formatted = []
                if results and "documents" in results and results["documents"]:
                    for i in range(len(results["ids"][0])):
                        formatted.append({
                            "id": results["ids"][0][i],
                            "text": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "score": 0.85 # Hardcoded distance score representation
                        })
                return formatted
            except Exception as e:
                logger.warning(f"ChromaDB search failed: {e}. Falling back to local search.")
        
        # Simple word-match fallback logic (mock semantic query)
        query_words = set(query.lower().split())
        matched = []
        for item in self.mock_store:
            # Score based on keyword overlap
            doc_words = set(item["text"].lower().split())
            intersection = query_words.intersection(doc_words)
            score = len(intersection) / len(query_words) if query_words else 0
            
            # Boost score if specific asset matches
            for word in query_words:
                if word in item["text"].lower():
                    score += 0.2
            
            matched.append((item, score))
        
        # Sort by score desc
        matched.sort(key=lambda x: x[1], reverse=True)
        return [
            {
                "id": item[0]["id"],
                "text": item[0]["text"],
                "metadata": item[0]["metadata"],
                "score": round(min(0.99, 0.4 + item[1]), 2)
            }
            for item in matched[:limit]
        ]
