import sqlite3
import json
import re
import time
import logging
from typing import List, Dict, Any, Tuple
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

# --- 1. LOGGING & AUDIT ---
class UserContextFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'user'): record.user = "SYSTEM"
        return True

logger = logging.getLogger("IndustrialAgent")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("security_audit.log")
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | USER:%(user)s | %(message)s"))
logger.addHandler(handler)
logger.addFilter(UserContextFilter())

# --- 2. CONFIGURATION & RBAC ---
DB_PATH = "Chinook.db"
SENSITIVE_COLUMNS = {"Password", "Fax", "Phone", "Address", "PostalCode"}

ROLE_TABLE_ACCESS = {
    "analyst": ["Album", "Artist", "Track", "Genre", "MediaType"],
    "finance": ["Invoice", "InvoiceLine", "Customer"],
    "admin": ["*"] 
}

# --- 3. CORE INDUSTRIAL ENGINE ---

class IndustrialAgent:
    def __init__(self, role: str):
        self.role = role
        self.schema = self._load_schema()
        self.llm = ChatOllama(model="qwen2.5:7b", temperature=0)

    def _load_schema(self):
        with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
            cursor = conn.cursor()
            tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            return {t: [c[1] for c in cursor.execute(f'PRAGMA table_info("{t}")').fetchall()] for t in tables}

    def _extract_json(self, response: str) -> Dict:
        clean = re.sub(r'```json\s?|\s?```', '', response).strip()
        match = re.search(r'\{.*\}', clean, re.DOTALL)
        if not match: raise ValueError("No JSON found.")
        return json.loads(match.group())

    def _validate_and_query(self, intent: Dict):
        """Industrial SQL Builder: Normalizes LLM Syntax Errors."""
        main_table = intent.get("table")
        join_table = intent.get("join_table")
        join_on = intent.get("join_on")
        cols = intent.get("columns", [])
        filter_col = intent.get("filter_column")
        filter_val = intent.get("filter_value")
        order_by = intent.get("order_by")

        # RBAC Check
        allowed = ROLE_TABLE_ACCESS.get(self.role, [])
        if "*" not in allowed and main_table not in allowed:
            raise PermissionError(f"Role '{self.role}' unauthorized for table '{main_table}'")

        # Syntax Normalization: Fix "Table.Table.Col" errors
        def normalize_col(c):
            parts = c.split(".")
            if len(parts) > 2: # Fixes Track.Album.AlbumId -> Album.AlbumId
                return f'"{parts[-2]}"."{parts[-1]}"'
            elif len(parts) == 2:
                return f'"{parts[0]}"."{parts[1]}"'
            return f'"{main_table}"."{c}"'

        formatted_cols = [normalize_col(c) for c in cols]
        col_str = ", ".join(formatted_cols) if formatted_cols else f'"{main_table}".*'
        
        sql = f'SELECT {col_str} FROM "{main_table}"'
        params = []

        # Secure Join
        if join_table and join_table in self.schema:
            if "*" in allowed or join_table in allowed:
                # Fix join_on if it contains extra dots
                clean_join_on = join_on.split(".")[-1]
                sql += f' JOIN "{join_table}" ON "{main_table}"."{clean_join_on}" = "{join_table}"."{clean_join_on}"'

        # Filter
        if filter_col and filter_val:
            clean_filter_col = filter_col.split(".")[-1]
            sql += f' WHERE "{main_table}"."{clean_filter_col}" LIKE ?'
            params.append(f"%{filter_val}%")

        if order_by:
            sql += f' ORDER BY {order_by}'

        sql += " LIMIT 10"
        
        with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
            return conn.execute(sql, params).fetchall()

    def ask(self, question: str):
        try:
            sys_msg = (
                f"Output ONLY JSON. Role: {self.role}. Schema: {json.dumps(self.schema)}\n"
                f"To find items by name, use 'filter_column' and 'filter_value'.\n"
                f"Example: {{\"table\": \"Track\", \"columns\": [\"Name\"], \"filter_column\": \"Name\", \"filter_value\": \"AC/DC\"}}"
            )
            
            resp = self.llm.invoke([SystemMessage(content=sys_msg), HumanMessage(content=question)]).content
            intent = self._extract_json(resp)
            data = self._validate_and_query(intent)
            
            logger.info(f"Query: {question}", extra={"user": self.role})
            return f"Results: {str(data)}"

        except Exception as e:
            logger.error(f"Error: {e}", extra={"user": self.role})
            return f"System Error: {str(e)}"

# --- 4. RUN ---
if __name__ == "__main__":
    print("\n--- SECURE INDUSTRIAL DATA AGENT v5 ---")
    u_role = input("Enter Role (analyst, finance, admin): ").strip().lower()
    agent = IndustrialAgent(u_role if u_role in ROLE_TABLE_ACCESS else "analyst")

    while True:
        query = input(f"\n[{u_role}] > ")
        if query.lower() in ["exit", "quit"]: break
        print(f"Assistant: {agent.ask(query)}")