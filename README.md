# Secure Data Agent - Industrial Role-Based Access Control System

A production-grade AI agent for secure database querying with **Role-Based Access Control (RBAC)**, **SQL injection prevention**, **audit logging**, and **LLM syntax error normalization**. Built with Ollama's qwen2.5:7b and SQLite.

## 🎯 Overview

The Secure Data Agent is an industrial-strength system that allows users to query databases naturally through conversation while maintaining strict security boundaries. It combines:

- **Role-Based Access Control (RBAC)** - Different users get different table access
- **SQL Injection Prevention** - Parameterized queries & syntax validation
- **Intelligent Error Recovery** - Fixes LLM-generated SQL syntax errors
- **Comprehensive Audit Logging** - Track all queries by user and role
- **Sensitive Data Protection** - Mask/restrict access to sensitive columns
- **LLM Integration** - Natural language to SQL via Ollama

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Ollama installed and running with qwen2.5:7b model
- SQLite database (uses Chinook.db by default)

### Installation

```bash
# Clone the repository
git clone https://github.com/TIRTHANATH20/secure-data-agent.git
cd secure-data-agent

# Install dependencies
pip install langchain-ollama langchain-core

# Ensure Ollama is running
ollama run qwen2.5:7b
```

### Running the Agent

```bash
python guardrails.py
```

You'll be prompted to select a role:

```
--- SECURE INDUSTRIAL DATA AGENT v5 ---
Enter Role (analyst, finance, admin): analyst

[analyst] > What are the top 5 albums?
```

## 📋 Features

### 1. **Role-Based Access Control**

Three built-in roles with different table access:

| Role | Access | Purpose |
|------|--------|---------|
| **analyst** | Album, Artist, Track, Genre, MediaType | Data analysis |
| **finance** | Invoice, InvoiceLine, Customer | Financial reports |
| **admin** | * (All tables) | Full database access |

**Example:**
```python
ROLE_TABLE_ACCESS = {
    "analyst": ["Album", "Artist", "Track", "Genre", "MediaType"],
    "finance": ["Invoice", "InvoiceLine", "Customer"],
    "admin": ["*"]
}
```

### 2. **SQL Injection Prevention**

- All queries use **parameterized statements**
- Sensitive columns are protected
- Unauthorized table access is blocked

**Protected Columns:**
```python
SENSITIVE_COLUMNS = {"Password", "Fax", "Phone", "Address", "PostalCode"}
```

### 3. **LLM Syntax Error Normalization**

The agent automatically fixes common SQL generation errors:

| Error Pattern | Fix |
|---------------|-----|
| `Track.Album.AlbumId` | `"Album"."AlbumId"` |
| Missing table prefixes | Auto-adds main table name |
| Malformed joins | Validates join syntax |

**Example:**
```python
# LLM generates: Track.Album.AlbumId
# System normalizes to: "Album"."AlbumId"
```

### 4. **Comprehensive Audit Logging**

All queries are logged to `security_audit.log` with:
- Timestamp
- Log level (INFO, ERROR, WARNING)
- User/Role
- Query details

**Log Example:**
```
2026-04-13 10:23:45,123 | INFO | USER:analyst | Query: What are the top 5 albums?
2026-04-13 10:24:12,456 | ERROR | USER:finance | Error: Role 'finance' unauthorized for table 'Track'
```

## 📁 Project Structure

```
secure-data-agent/
├── guardrails.py           # Main agent implementation
├── Chinook.db             # SQLite database (music store sample)
├── security_audit.log     # Audit trail (generated on first run)
├── README.md              # This file
└── .gitignore             # Git ignore rules
```

## 🔧 Usage

### Basic Query

```python
agent = IndustrialAgent(role="analyst")
result = agent.ask("Show me all tracks by AC/DC")
# Returns: Results: [(1, 'Back in Black', ...)]
```

### Role-Based Access

```python
# Analyst can only query music data
analyst = IndustrialAgent("analyst")
analyst.ask("Show invoices")  # ❌ PermissionError

# Finance can query only financial data
finance = IndustrialAgent("finance")
finance.ask("Show invoices by customer")  # ✅ Success

# Admin can query anything
admin = IndustrialAgent("admin")
admin.ask("Show all data")  # ✅ Success
```

### Interactive Session

```bash
$ python guardrails.py
--- SECURE INDUSTRIAL DATA AGENT v5 ---
Enter Role (analyst, finance, admin): analyst

[analyst] > What albums are by The Beatles?
Assistant: Results: [(1, 'Abbey Road'), (2, 'Help!')]

[analyst] > Show me the top 10 tracks by plays
Assistant: Results: [(...), (...)]

[analyst] > exit
```

## 🏗️ Architecture

### 1. **UserContextFilter** - Logging

Enriches log records with user context:
```python
logger.info("Query executed", extra={"user": "analyst"})
# Output: "... | USER:analyst | Query executed"
```

### 2. **IndustrialAgent** - Core Engine

Manages:
- Schema loading from SQLite
- LLM communication via Ollama
- JSON extraction from LLM responses
- Query validation and normalization
- RBAC enforcement

### 3. **SQL Builder** - `_validate_and_query()`

Converts LLM output to secure SQL:

```
LLM Output (JSON)
    ↓
[Normalize Column Names]
    ↓
[Validate Table Access (RBAC)]
    ↓
[Build SQL with Parameterization]
    ↓
[Execute & Return Results]
```

## 📝 Configuration

### Adding Custom Roles

Edit the `ROLE_TABLE_ACCESS` dictionary:

```python
ROLE_TABLE_ACCESS = {
    "analyst": ["Album", "Artist", "Track", "Genre", "MediaType"],
    "finance": ["Invoice", "InvoiceLine", "Customer"],
    "admin": ["*"],
    "hr": ["Employee"],  # New role
}
```

### Changing the Database

Replace the `DB_PATH`:

```python
DB_PATH = "path/to/your/database.db"
```

### Using a Different LLM Model

Edit the ChatOllama initialization:

```python
self.llm = ChatOllama(model="llama2", temperature=0)
```

### Protecting Additional Columns

Add to `SENSITIVE_COLUMNS`:

```python
SENSITIVE_COLUMNS = {
    "Password", "Fax", "Phone", "Address", 
    "PostalCode", "Email", "SSN"  # New protected columns
}
```

## 🔐 Security Features

### 1. **SQL Injection Prevention**

```python
# ❌ Vulnerable
cursor.execute(f"SELECT * FROM Track WHERE Name = '{user_input}'")

# ✅ Secure (used in this project)
cursor.execute('SELECT * FROM "Track" WHERE "Track"."Name" LIKE ?', (user_input,))
```

### 2. **Role-Based Access**

```python
def _validate_and_query(self, intent: Dict):
    allowed = ROLE_TABLE_ACCESS.get(self.role, [])
    if "*" not in allowed and main_table not in allowed:
        raise PermissionError(f"Role '{self.role}' unauthorized for table '{main_table}'")
```

### 3. **Read-Only Database Access**

```python
# Opens database in read-only mode
with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
```

### 4. **Audit Trail**

Every query is logged with timestamp, user, role, and outcome.

## 🐛 Troubleshooting

**Issue**: "Connection refused on Ollama"
- Solution: Ensure Ollama is running: `ollama serve`

**Issue**: "Model 'qwen2.5:7b' not found"
- Solution: Download model: `ollama pull qwen2.5:7b`

**Issue**: "PermissionError: unauthorized for table"
- Solution: Your role doesn't have access. Check `ROLE_TABLE_ACCESS`

**Issue**: "No JSON found" when parsing LLM response
- Solution: The LLM didn't return valid JSON. Check model output and adjust system prompt

**Issue**: Database locked or read-only
- Solution: Ensure `Chinook.db` exists and is readable. Use absolute path if needed.

**Issue**: Column names not found in results
- Solution: Check table schema via: `SELECT * FROM sqlite_master WHERE type='table'`

## 📊 Example Use Cases

### Analytics Team (analyst role)
```
[analyst] > Which artists have the most tracks?
[analyst] > Show me the genre distribution in our catalog
[analyst] > What are the most popular tracks by play count?
```

### Finance Team (finance role)
```
[finance] > What's our total revenue by customer?
[finance] > Show pending invoices
[finance] > Which customers spent over $100?
```

### System Administrators (admin role)
```
[admin] > Show me all database activity
[admin] > Export complete customer list
[admin] > List all tables and their row counts
```

## 🔧 Advanced: Custom Checkers

Extend the system with custom query validators:

```python
class CustomValidator:
    @staticmethod
    def validate_date_range(intent: Dict):
        """Ensure date queries are within reasonable range"""
        start = intent.get("start_date")
        end = intent.get("end_date")
        if start and end:
            days = (end - start).days
            if days > 365:
                raise ValueError("Date range exceeds 1 year")
        return True

# Add to _validate_and_query():
CustomValidator.validate_date_range(intent)
```

## 📈 Performance Optimization

The agent includes built-in optimizations:

- **LIMIT 10** on all queries - Prevents overwhelming results
- **Parameterized queries** - Reduces parsing overhead
- **Schema caching** - Loads database schema once on initialization
- **Read-only mode** - Optimized for queries, not writes

## 🤖 How It Works

1. **User asks a question** in natural language
2. **System message** describes schema and role permissions
3. **LLM generates JSON** with query intent
4. **JSON extraction** parses the response
5. **Normalization** fixes SQL syntax errors
6. **RBAC validation** checks role permissions
7. **Query execution** with parameterized SQL
8. **Audit logging** records the interaction
9. **Results returned** to user

## 📚 Database Schema (Chinook)

The system works with the Chinook music database:

```
Artists → Albums → Tracks → PlaylistTracks → Playlists
            ↓
          Genres
          
Customers → Invoices → InvoiceLines → Tracks
```

Perfect for testing music industry queries!

## 🛠️ Dependencies

```
langchain-ollama>=0.0.1
langchain-core>=0.0.1
sqlite3 (built-in)
logging (built-in)
json (built-in)
re (built-in)
```

## 📄 License

This project is part of the RESPONSIBLE initiative for responsible AI development.

## 👤 Author

TIRTHANATH20

## 🤝 Contributing

To contribute improvements:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make changes
4. Add tests or audit logs showing the improvement
5. Submit a pull request

## 📧 Support

For issues, questions, or suggestions, please open a GitHub issue.

---

**Status**: Production Ready ✨  
**Last Updated**: April 2026  
**Version**: 5.0.0  
**Security Level**: Enterprise-Grade  
