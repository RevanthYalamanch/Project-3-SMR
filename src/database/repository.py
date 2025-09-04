import sqlite3
from pydantic import BaseModel
from typing import List, Optional
import numpy as np

# The Profile class remains the same
class Profile(BaseModel):
    name: str
    role: str
    bio: Optional[str] = ""
    photo_url: Optional[str] = None

class ProfileRepository:
    def __init__(self, db_path: str):
        # We only store the path now, we don't connect here.
        self.db_path = db_path

    def _get_connection(self):
        """Helper method to create a new connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self):
        """Creates the necessary tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                role TEXT,
                bio TEXT,
                photo_url TEXT
            )
            ''')
            cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS profiles_fts USING fts5(
                name, role, bio, content='profiles', content_rowid='id'
            )
            ''')
            conn.commit()

    def add_profile(self, profile: Profile):
        """Adds a single profile to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                INSERT INTO profiles (name, role, bio, photo_url)
                VALUES (?, ?, ?, ?)
                ''', (profile.name, profile.role, profile.bio, str(profile.photo_url) if profile.photo_url else None))
                
                rowid = cursor.lastrowid
                cursor.execute('''
                INSERT INTO profiles_fts (rowid, name, role, bio)
                VALUES (?, ?, ?, ?)
                ''', (rowid, profile.name, profile.role, profile.bio))
                conn.commit()
            except sqlite3.IntegrityError:
                print(f"Profile for {profile.name} already exists. Skipping.")

    def get_all_profiles(self) -> List[Profile]:
        """Retrieves all profiles."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, role, bio, photo_url FROM profiles ORDER BY name")
            rows = cursor.fetchall()
            return [Profile(**row) for row in rows]

    def search_profiles(self, keyword: str) -> List[Profile]:
        """Performs a keyword-based search."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT p.name, p.role, p.bio, p.photo_url
            FROM profiles p JOIN profiles_fts fts ON p.id = fts.rowid
            WHERE profiles_fts MATCH ? ORDER BY rank
            ''', (keyword,))
            rows = cursor.fetchall()
            return [Profile(**row) for row in rows]

    def get_all_profiles_for_indexing(self) -> List[dict]:
        """Retrieves all profiles with their ID, name, and content."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, role, bio FROM profiles ORDER BY name")
            rows = cursor.fetchall()
            # CORRECTED: Added "name": row["name"] to the dictionary
            return [
                {
                    "id": row["id"], 
                    "name": row["name"], 
                    "content": f"{row['name']} {row['role']} {row['bio']}"
                } 
                for row in rows
            ]

    def get_profiles_by_ids(self, ids: np.ndarray) -> List[Profile]:
        """Retrieves specific profiles by their IDs, preserving order."""
        if not ids.any():
            return []
        
        id_list = ids.tolist() # Convert numpy array to list for the query

        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ', '.join('?' for _ in id_list)
            query = f"SELECT id, name, role, bio, photo_url FROM profiles WHERE id IN ({placeholders})"
            cursor.execute(query, id_list)
            rows = cursor.fetchall()
            
            profile_map = {row["id"]: Profile(**dict(row)) for row in rows}
            ordered_profiles = [profile_map[id] for id in id_list if id in profile_map]
            return ordered_profiles
        
    
    def get_profile_by_id(self, profile_id: int) -> Optional[Profile]:
        """Retrieves a single profile by its primary key ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, role, bio, photo_url FROM profiles WHERE id = ?", (profile_id,))
            row = cursor.fetchone()
            return Profile(**row) if row else None

    def update_profile(self, profile_id: int, profile: Profile):
        """Updates an existing profile in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE profiles SET name=?, role=?, bio=?, photo_url=?
            WHERE id=?
            ''', (profile.name, profile.role, profile.bio, str(profile.photo_url), profile_id))
            
            cursor.execute('''
            UPDATE profiles_fts SET name=?, role=?, bio=?
            WHERE rowid=?
            ''', (profile.name, profile.role, profile.bio, profile_id))
            conn.commit()

    def delete_profile(self, profile_id: int):
        """Deletes a profile from the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM profiles WHERE id=?", (profile_id,))
            cursor.execute("DELETE FROM profiles_fts WHERE rowid=?", (profile_id,))
            conn.commit()

     # --- NEW METHODS FOR MILESTONE 5 ---
    def get_all_profiles_as_dicts(self) -> List[dict]:
        """Retrieves all profiles as a list of dictionaries for JSON export."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, role, bio, photo_url FROM profiles ORDER BY name")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def import_from_json_data(self, profiles_data: List[dict]):
        """Deletes all existing data and imports new profiles from a list of dicts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            print("Deleting all existing profiles...")
            cursor.execute("DELETE FROM profiles")
            cursor.execute("DELETE FROM profiles_fts")
            
            print(f"Importing {len(profiles_data)} new profiles...")
            for profile_dict in profiles_data:
                profile = Profile(**profile_dict) # Validate with Pydantic
                try:
                    cursor.execute(
                        "INSERT INTO profiles (name, role, bio, photo_url) VALUES (?, ?, ?, ?)",
                        (profile.name, profile.role, profile.bio, str(profile.photo_url) if profile.photo_url else None)
                    )
                    rowid = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO profiles_fts (rowid, name, role, bio) VALUES (?, ?, ?, ?)",
                        (rowid, profile.name, profile.role, profile.bio)
                    )
                except sqlite3.IntegrityError:
                    print(f"Skipping duplicate profile on import: {profile.name}")
            
            conn.commit()