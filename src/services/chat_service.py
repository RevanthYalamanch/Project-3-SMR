import streamlit as st
import google.generativeai as genai
from src.database.repository import ProfileRepository
from src.search.vector_search import VectorSearch
from typing import List

class ChatService:
    def __init__(self, repo: ProfileRepository, search: VectorSearch):
        self.repo = repo
        self.search = search
        # Securely configure the Gemini API key from Streamlit's secrets
        self.google_api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=self.google_api_key)

    def is_in_scope(self, query: str) -> bool:
        """
        A simple rule-based function to check if a query is in scope.
        """
        scope_keywords = [
            'who', 'ceo', 'team', 'leadership', 'director',
            'head', 'manager', 'executive', 'founder', 'president',
            'role', 'background', 'experience', 'profile', 'about'
        ]
        return any(keyword in query.lower() for keyword in scope_keywords)

    def get_rag_response(self, query: str) -> str:
        """
        Generates a response using the RAG pipeline with Google's Gemini Pro model.
        """
        # 1. Scope Check
        if not self.is_in_scope(query):
            return "I'm sorry, I only have information about the Amzur leadership team. I can't help with questions about other topics. Try asking something like 'Who is the CEO?'"

        # 2. Retrieval
        distances, db_ids = self.search.search(query, top_k=3)
        retrieved_profiles = self.repo.get_profiles_by_ids(db_ids)

        if not retrieved_profiles:
            return "I couldn't find any specific profiles related to your question, but I can tell you about the leadership team in general."

        # 3. Augment (Create the prompt)
        context = "\n\n".join([f"Name: {p.name}\nRole: {p.role}\nBio: {p.bio}" for p in retrieved_profiles])
        
        prompt = f"""
        You are a helpful assistant for Amzur. Your knowledge is strictly limited to the information provided below about the company's leadership team.
        Do not answer any questions outside of this context. If the information is not in the context, say you don't have that specific detail.
        
        Context:
        ---
        {context}
        ---

        Question: {query}

        Answer:
        """
        
        # 4. Generate with Gemini
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"An error occurred with the Google AI service: {e}")
            return "Sorry, I'm having trouble connecting to the AI service right now."