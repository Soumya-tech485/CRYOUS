import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Firebase for OS State & Config
import firebase_admin
from firebase_admin import credentials, firestore

# Pinecone & Embeddings for the "Hive Mind" RAG
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

class HiveMind:
    def __init__(self):
        load_dotenv()
        
        # 1. Initialize State Manager (Firebase)
        self._init_firebase()
        
        # 2. Initialize Semantic Core (Pinecone + Local Embeddings)
        self._init_vector_store()
        
    def _init_firebase(self):
        """Initializes Firebase Firestore for syncing OS configurations across instances."""
        try:
            # Requires a service_account.json from your Firebase Console
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "config/service_account.json")
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            print("[System] Firebase State Manager: ONLINE")
        except Exception as e:
            print(f"[Warning] Firebase initialization failed. State sync offline. Details: {e}")
            self.db = None

    def _init_vector_store(self):
        """Initializes Pinecone and the local embedding model for RAG."""
        try:
            # We use an extremely fast, lightweight local model to generate vectors 
            # so we don't have to wait for an API call to embed text.
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
            pc_api_key = os.getenv("PINECONE_API_KEY")
            if not pc_api_key:
                raise ValueError("PINECONE_API_KEY missing from environment.")
                
            self.pc = Pinecone(api_key=pc_api_key)
            self.index_name = "cryous-hive-mind"
            
            # Create the vector index if it doesn't exist
            if self.index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384, # Dimension size for 'all-MiniLM-L6-v2'
                    metric='cosine',
                    spec=ServerlessSpec(cloud='aws', region='us-east-1')
                )
            
            self.index = self.pc.Index(self.index_name)
            print("[System] Pinecone Semantic Core: ONLINE")
        except Exception as e:
            print(f"[Warning] Vector Store initialization failed. RAG offline. Details: {e}")
            self.index = None

    # --- FIREBASE: STATE MANAGEMENT ---

    def update_os_state(self, instance_id: str, state_data: dict):
        """Syncs the current operational state of this OS instance to the cloud."""
        if not self.db:
            return False
        try:
            self.db.collection("instances").document(instance_id).set(state_data, merge=True)
            return True
        except Exception as e:
            print(f"[Error] Failed to sync state: {e}")
            return False

    def get_global_config(self) -> dict:
        """Fetches global settings shared across all CRYOUS instances."""
        if not self.db:
            return {}
        try:
            doc = self.db.collection("config").document("global").get()
            return doc.to_dict() if doc.exists else {}
        except Exception:
            return {}

    # --- PINECONE: HIVE MIND RAG ---

    def memorize(self, text_data: str, metadata: dict = None):
        """
        Converts text into a vector embedding and uploads it to the Hive Mind.
        Any OS instance can now recall this information.
        """
        if not self.index:
            return "[Error] Semantic Core offline."
            
        try:
            # 1. Convert text to a mathematical vector
            vector = self.embedder.encode(text_data).tolist()
            
            # 2. Generate a unique ID (could be a hash of the text)
            doc_id = str(hash(text_data))
            
            # 3. Store in the cloud vector database
            meta = metadata if metadata else {}
            meta["raw_text"] = text_data # Store the original text to retrieve later
            
            self.index.upsert(vectors=[{"id": doc_id, "values": vector, "metadata": meta}])
            return "[Success] Information committed to Hive Mind."
        except Exception as e:
            return f"[Error] Memory storage failed: {e}"

    def recall(self, query: str, top_k: int = 3) -> List[str]:
        """
        Searches the Hive Mind for knowledge mathematically similar to the query.
        Returns the raw text strings to be injected into the Groq prompt.
        """
        if not self.index:
            return []
            
        try:
            # Embed the search query
            query_vector = self.embedder.encode(query).tolist()
            
            # Query Pinecone for the closest matching vectors
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )
            
            # Extract the raw text from the metadata of the closest matches
            retrieved_context = [match['metadata']['raw_text'] for match in results['matches']]
            return retrieved_context
        except Exception as e:
            print(f"[Error] Memory recall failed: {e}")
            return []
        