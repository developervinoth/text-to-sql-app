# models/database.py
import sqlite3
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

@dataclass
class TableSchema:
    """Represents database table schema information"""
    name: str
    columns: List[Dict[str, str]]
    sample_data: List[Dict[str, Any]]
    foreign_keys: List[Dict[str, str]]
    description: str = ""

@dataclass
class ColumnDescription:
    """Represents column description metadata"""
    table_name: str
    column_name: str
    description: str
    business_meaning: str = ""
    data_examples: str = ""

class DatabaseManager:
    """Handles database connections and operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection = None
    
    @property
    def connection(self):
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a query and return results"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def execute_write(self, query: str, params: tuple = ()) -> int:
        """Execute a write query and return affected rows"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor.rowcount