import sqlite3
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from contextlib import contextmanager
from typing import Generator
from app.core.settings import settings

from pathlib import Path
from sqlalchemy.pool import NullPool

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

# We delay engine creation to get_db() to support test fixtures overriding DATABASE_PATH
def get_engine():
    url = settings.DATABASE_URL
    if settings.DATABASE_PATH and url.startswith("sqlite") and "memory" not in url:
        # Convert path properly for Windows SQLAlchemy compatibility
        db_path = Path(settings.DATABASE_PATH).absolute().as_posix()
        url = f"sqlite:///{db_path}"
    return create_engine(url, poolclass=NullPool)
class MockRow:
    def __init__(self, mapping, tuple_row):
        self._mapping = mapping
        self._tuple_row = tuple_row
        
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._tuple_row[key]
        return self._mapping[key]
        
    def keys(self):
        return self._mapping.keys()

    def get(self, key, default=None):
        if key in self._mapping:
            return self._mapping[key]
        return default

    def __iter__(self):
        return iter(self._mapping)

class LegacyCursorWrapper:
    def __init__(self, result):
        self.result = result

    def fetchone(self):
        if not self.result: return None
        row = self.result.fetchone()
        if row is None: return None
        return MockRow(row._mapping, row._tuple())

    def fetchall(self):
        if not self.result: return []
        return [MockRow(row._mapping, row._tuple()) for row in self.result.fetchall()]

    @property
    def lastrowid(self):
        # Fallback for lastrowid
        if hasattr(self.result, 'lastrowid'):
            return self.result.lastrowid
        return None

class DBWrapper:
    def __init__(self, session: Session):
        self.session = session
        
    def _convert_query(self, query: str, args: tuple):
        if not args:
            return query, {}
            
        new_query = ""
        params = {}
        param_idx = 0
        in_single_quote = False
        in_double_quote = False
        
        for i, char in enumerate(query):
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                
            if char == '?' and not in_single_quote and not in_double_quote:
                pname = f"p_{param_idx}"
                new_query += f":{pname}"
                params[pname] = args[param_idx]
                param_idx += 1
            else:
                new_query += char
                
        return new_query, params

    def _postgres_dialect_fix(self, query: str) -> str:
        if "postgresql" in settings.DATABASE_URL:
            # Basic fixes for sqlite syntax that breaks on postgres
            query = query.replace("INSERT OR IGNORE INTO", "INSERT INTO")
            # Handling ON CONFLICT is complex for a regex, so we'll just remove OR IGNORE and let it fail if conflicts arise, 
            # or fix the specific queries in the codebase.
        return query

    def execute(self, query: str, args=None):
        if args is None:
            args = ()
        # Convert ? to named parameters
        new_query, params = self._convert_query(query, args)
        new_query = self._postgres_dialect_fix(new_query)
        
        result = self.session.execute(text(new_query), params)
        return LegacyCursorWrapper(result)

    def executemany(self, query: str, args_list: list):
        for args in args_list:
            self.execute(query, args)

    def executescript(self, script: str):
        # Extremely basic script execution
        for stmt in script.split(';'):
            stmt = stmt.strip()
            if stmt:
                self.session.execute(text(stmt))
        
    def commit(self):
        self.session.commit()
        
    def rollback(self):
        self.session.rollback()

@contextmanager
def get_db() -> Generator[DBWrapper, None, None]:
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield DBWrapper(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
