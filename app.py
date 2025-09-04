import streamlit as st
import json
import pandas as pd
import plotly.express as px
from src.database.repository import ProfileRepository, Profile
from src.search.vector_search import VectorSearch
from src.services.chat_service import ChatService

DB_PATH = "data/profiles.db"
FAISS_INDEX_PATH = "data/profiles.faiss"

st.set_page_config(page_title="Smart Knowledge Repository", layout="wide")
st.title("🤖 Smart Knowledge Repository")

@st.cache_resource
def load_resources():
    repo = ProfileRepository(db_path=DB_PATH)
    vector_search = VectorSearch()
    vector_search.load_index(FAISS_INDEX_PATH)
    chat_service = ChatService(repo, vector_search)
    return repo, chat_service, vector_search

try:
    repo, chat_service, vector_search = load_resources()
except Exception as e:
    st.error(f"An error occurred during initialization: {e}")
    st.info("Please make sure you have run `create_index.py` and have a valid `.streamlit/secrets.toml` file.")
    st.stop()

# --- UI Tabs ---
chat_tab, browse_tab, admin_tab, analytics_tab = st.tabs(["💬 Chat Assistant", "📚 Browse Profiles", "⚙️ Admin Dashboard", "📊 Analytics"])

with chat_tab:
    # This code remains the same as Milestone 3
    st.header("Chat with the AI Assistant")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Ask a question..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Thinking..."):
            response = chat_service.get_rag_response(prompt)
            with st.chat_message("assistant"):
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

with browse_tab:
    # This code remains the same as Milestone 4
    st.header("Browse and Search Profiles")
    def display_profiles(profiles):
        if not profiles: st.warning("No profiles found.")
        for p in profiles:
            if p.photo_url: st.image(str(p.photo_url), width=150)
            st.subheader(p.name); st.caption(p.role)
            with st.expander("View Bio"): st.write(p.bio if p.bio else "No bio available.")
            st.divider()
    search_query = st.text_input("Search by keyword:", key="browse_search")
    if search_query: display_profiles(repo.search_profiles(search_query))
    else: display_profiles(repo.get_all_profiles())

with admin_tab:
    # This code is updated with Export/Import functionality
    st.header("Knowledge Base Management")
    profiles_for_admin = repo.get_all_profiles_for_indexing()
    profile_options = {p['id']: p['name'] for p in profiles_for_admin}
    action = st.selectbox("Choose an action", ["View All", "Add New Profile", "Edit Profile", "Delete Profile"])

    # ... (Add, Edit, Delete forms remain the same as Milestone 4) ...

    st.divider()
    st.subheader("Backup and Restore")

    # Export Functionality
    try:
        all_profiles_dicts = repo.get_all_profiles_as_dicts()
        json_string = json.dumps(all_profiles_dicts, indent=2)
        st.download_button(
            label="📥 Export Knowledge Base to JSON",
            file_name="knowledge_base_backup.json",
            mime="application/json",
            data=json_string,
        )
    except Exception as e:
        st.error(f"Could not prepare export data: {e}")

    # Import Functionality
    uploaded_file = st.file_uploader("Import Knowledge Base from JSON", type=["json"])
    if uploaded_file is not None:
        try:
            new_data = json.load(uploaded_file)
            st.warning("⚠️ Warning: Importing will overwrite all existing data in the database.")
            if st.button("Confirm and Import Data"):
                repo.import_from_json_data(new_data)
                st.success("Successfully imported data from file.")
                st.info("Important: You must run `create_index.py` again to update the semantic search with the new data.")
                st.experimental_rerun()
        except Exception as e:
            st.error(f"An error occurred during import: {e}")

with analytics_tab:
    st.header("Knowledge Base Analytics")
    
    profiles_data = repo.get_all_profiles()
    if profiles_data:
        df = pd.DataFrame([p.dict() for p in profiles_data])
        
        st.subheader("Profiles per Role")
        role_counts = df['role'].value_counts().reset_index()
        role_counts.columns = ['Role', 'Count']
        
        fig = px.bar(role_counts, x='Role', y='Count', title="Number of Profiles by Role", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Raw Data View")
        st.dataframe(df)
    else:
        st.warning("No data in the knowledge base to analyze.")