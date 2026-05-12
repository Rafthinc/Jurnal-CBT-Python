import os
import json
from typing import List, Dict, Any
from src.domain.models import CBTEntry
from supabase import create_client, Client
import streamlit as st

class DatabaseService:
    def __init__(self):
        # Read from Streamlit secrets (which you will configure in the Cloud)
        # Fallback to empty strings to avoid hard crashes if secrets are missing
        self.supabase_url: str = st.secrets.get("SUPABASE_URL", "https://pvixdquoynxsdecmcnmt.supabase.co")
        self.supabase_key: str = st.secrets.get("SUPABASE_KEY", "sb_publishable_70-ue3HnLLkLmKmx50dNnA_cb4E0BfE")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    def load_users_for_auth(self) -> Dict[str, Any]:
        """Loads users in the format expected by streamlit-authenticator"""
        try:
            # Note: We are using a custom 'users' table, NOT the built-in Supabase Auth auth.users, 
            # because we want to keep compatibility with streamlit-authenticator for now.
            response = self.supabase.table('users').select("*").execute()
            users = response.data
        except Exception as e:
            st.error(f"Error connecting to Supabase: {e}")
            return {"usernames": {}}
            
        credentials = {"usernames": {}}
        for u in users:
            username = u.get("username")
            credentials["usernames"][username] = {
                "email": u.get("email"),
                "name": u.get("name"),
                "password": u.get("password_hash")
            }
        return credentials

    def save_user(self, username: str, email: str, name: str, password_hash: str):
        data = {
            "username": username,
            "email": email,
            "name": name,
            "password_hash": password_hash
        }
        # Upsert user data
        self.supabase.table('users').upsert(data).execute()

    def add_cbt_entry(self, username: str, entry: CBTEntry):
        emotii_json = json.dumps(entry.emotii)
        data = {
            "username": username,
            "situatie": entry.situatie,
            "ganduri": entry.ganduri,
            "veridicitate_ganduri": entry.veridicitate_ganduri,
            "emotii": emotii_json,
            "intensitate_emotie": entry.intensitate_emotie,
            "comportament": entry.comportament,
            "data_creare": entry.data_creare
        }
        self.supabase.table('cbt_entries').insert(data).execute()

    def get_user_entries(self, username: str) -> List[CBTEntry]:
        response = self.supabase.table('cbt_entries').select("*").eq('username', username).order('id', desc=False).execute()
        rows = response.data
            
        entries = []
        for row in rows:
            emotii = json.loads(row.get("emotii", "[]"))
            entries.append(CBTEntry(
                situatie=row.get("situatie", ""),
                ganduri=row.get("ganduri", ""),
                veridicitate_ganduri=row.get("veridicitate_ganduri", 0),
                emotii=emotii,
                intensitate_emotie=row.get("intensitate_emotie", 0),
                comportament=row.get("comportament", ""),
                data_creare=row.get("data_creare", "")
            ))
        return entries

    def get_admin_stats(self) -> tuple:
        # Count total users
        response_users = self.supabase.table('users').select('*', count='exact').execute()
        total_users = response_users.count if response_users.count is not None else len(response_users.data)
        
        # Count total CBT entries
        response_entries = self.supabase.table('cbt_entries').select('*', count='exact').execute()
        total_entries = response_entries.count if response_entries.count is not None else len(response_entries.data)
        
        # Get list of all users
        users_data = []
        for u in response_users.data:
            users_data.append((u.get("username"), u.get("email"), u.get("name")))
            
        return total_users, total_entries, users_data