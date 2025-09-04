from src.database.repository import ProfileRepository
from src.search.vector_search import VectorSearch

DB_PATH = "data/profiles.db"
FAISS_INDEX_PATH = "data/profiles.faiss"

def run_indexing_pipeline():
    """
    Creates vector embeddings and a FAISS index from the profiles in the database.
    """
    print("--- Starting Vector Indexing Pipeline ---")

    repo = ProfileRepository(db_path=DB_PATH)
    profiles_to_index = repo.get_all_profiles_for_indexing()

    if not profiles_to_index:
        print("No profiles found in the database to index.")
        return

    # Extract the content and original database IDs for indexing
    contents = [p['content'] for p in profiles_to_index]
    db_ids = [p['id'] for p in profiles_to_index]

    vector_search = VectorSearch()
    embeddings = vector_search.create_embeddings(contents)
    vector_search.create_and_save_index(embeddings, db_ids, FAISS_INDEX_PATH)
    
    print("--- Vector Indexing Pipeline Finished ---")

if __name__ == "__main__":
    run_indexing_pipeline()