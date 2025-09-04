import streamlit as st
from src.database.repository import ProfileRepository, Profile
from src.search.vector_search import VectorSearch # New import
from typing import List

DB_PATH = "data/profiles.db"
FAISS_INDEX_PATH = "data/profiles.faiss"

# --- Cache the resources to avoid reloading on every interaction ---
@st.cache_resource
def load_resources():
    repo = ProfileRepository(db_path=DB_PATH)
    vector_search = VectorSearch()
    vector_search.load_index(FAISS_INDEX_PATH)
    return repo, vector_search

def display_profiles(profiles: List[Profile]):
    # This function is the same as before
    if not profiles:
        st.warning("No profiles found.")
        return
    for profile in profiles:
        if profile.photo_url:
            st.image(str(profile.photo_url), width=150)
        st.subheader(profile.name)
        st.caption(profile.role)
        with st.expander("View Bio"):
            st.write(profile.bio if profile.bio else "No bio available.")
        st.divider()

def main():
    st.set_page_config(layout="wide")
    st.title("👨‍💼 Amzur Knowledge Repository")

    try:
        repo, vector_search = load_resources()
    except FileNotFoundError:
        st.error(f"Error: The index file was not found at {FAISS_INDEX_PATH}.")
        st.error("Please run the `create_index.py` script first to generate the search index.")
        return

    # UI with tabs for different views
    tab1, tab2, tab3 = st.tabs(["🧠 Semantic Search", "🔎 Keyword Search", "📚 Browse All"])

    with tab1:
        st.header("Semantic Search")
        st.info("This search understands the *meaning* of your query. Try asking a question like 'Who has experience with business strategy?'")
        semantic_query = st.text_input("Enter a question or topic:", key="semantic")

        if semantic_query:
            distances, db_ids = vector_search.search(semantic_query)
            # We get back the original database IDs directly from FAISS
            results = repo.get_profiles_by_ids(db_ids)
            st.write(f"Found **{len(results)}** semantically similar profiles:")
            display_profiles(results)

    with tab2:
        st.header("Keyword Search")
        keyword_query = st.text_input("Enter a name, role, or keyword to search:", key="keyword")
        if keyword_query:
            results = repo.search_profiles(keyword_query)
            st.write(f"Found **{len(results)}** matching profiles:")
            display_profiles(results)

    with tab3:
        st.header("All Leadership Profiles")
        all_profiles = repo.get_all_profiles()
        display_profiles(all_profiles)

if __name__ == "__main__":
    main()