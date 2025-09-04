import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List

class VectorSearch:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """Initializes the model for creating vector embeddings."""
        self.model = SentenceTransformer(model_name)
        self.index = None

    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Converts a list of texts into a matrix of vector embeddings."""
        print("Creating text embeddings...")
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.astype('float32') # FAISS requires float32

    def create_and_save_index(self, embeddings: np.ndarray, db_ids: List[int], file_path: str):
        """Builds a FAISS index that maps vectors to their database IDs and saves it."""
        print(f"Creating FAISS index for {len(embeddings)} vectors...")
        dimension = embeddings.shape[1]
        # Using a simple L2 distance index
        index = faiss.IndexFlatL2(dimension)
        # Wrapping it with IndexIDMap to store our original database IDs
        self.index = faiss.IndexIDMap(index)
        
        # FAISS requires a numpy array of int64 for IDs
        ids_array = np.array(db_ids).astype('int64')
        self.index.add_with_ids(embeddings, ids_array)
        
        print(f"Saving index to {file_path}...")
        faiss.write_index(self.index, file_path)

    def load_index(self, file_path: str):
        """Loads a pre-built FAISS index from a file."""
        print(f"Loading FAISS index from {file_path}...")
        self.index = faiss.read_index(file_path)

    def search(self, query_text: str, top_k: int = 5) -> tuple[np.ndarray, np.ndarray]:
        """
        Searches the index for the top_k most similar items to the query_text.
        Returns distances and the original database IDs.
        """
        if self.index is None:
            raise RuntimeError("Index is not loaded. Please load an index before searching.")
            
        query_vector = self.model.encode([query_text]).astype('float32')
        distances, db_ids = self.index.search(query_vector, top_k)
        return distances[0], db_ids[0]