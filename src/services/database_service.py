import sqlite3
import os
from typing import List, Dict, Any
import json
from src.domain.models import CBTEntry

class DatabaseService:
    def __init__(self, db_path="cbt_data.db"):
        self.db_path = db_path
        self._create_tables()
        
    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    email TEXT,
                    name TEXT,
                    password_hash TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cbt_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    situatie TEXT,
                    ganduri TEXT,
                    veridicitate_ganduri INTEGER,
                    emotii TEXT,  -- JSON string list
                    intensitate_emotie INTEGER,
                    comportament TEXT,
                    data_creare TEXT,
                    FOREIGN KEY(username) REFERENCES users(username)
                )
            ''')
            conn.commit()

    def load_users_for_auth(self) -> Dict[str, Any]:
        """Loads users in the format expected by streamlit-authenticator"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, email, name, password_hash FROM users")
            users = cursor.fetchall()
            
        credentials = {"usernames": {}}
        for u in users:
            username, email, name, pwd_hash = u
            credentials["usernames"][username] = {
                "email": email,
                "name": name,
                "password": pwd_hash
            }
        return credentials

    def save_user(self, username: str, email: str, name: str, password_hash: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (username, email, name, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (username, email, name, password_hash))
            conn.commit()

    def add_cbt_entry(self, username: str, entry: CBTEntry):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            emotii_json = json.dumps(entry.emotii)
            cursor.execute('''
                INSERT INTO cbt_entries (username, situatie, ganduri, veridicitate_ganduri, emotii, intensitate_emotie, comportament, data_creare)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                username, entry.situatie, entry.ganduri, entry.veridicitate_ganduri,
                emotii_json, entry.intensitate_emotie, entry.comportament, entry.data_creare
            ))
            conn.commit()

    def get_user_entries(self, username: str) -> List[CBTEntry]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Order by id to keep chronological insertion order
            cursor.execute('''
                SELECT situatie, ganduri, veridicitate_ganduri, emotii, intensitate_emotie, comportament, data_creare
                FROM cbt_entries
                WHERE username = ?
                ORDER BY id ASC
            ''', (username,))
            rows = cursor.fetchall()
            
        entries = []
        for row in rows:
            emotii = json.loads(row[3])
            entries.append(CBTEntry(
                situatie=row[0],
                ganduri=row[1],
                veridicitate_ganduri=row[2],
                emotii=emotii,
                intensitate_emotie=row[4],
                comportament=row[5],
                data_creare=row[6]
            ))
        return entries
