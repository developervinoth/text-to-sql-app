# ============================================================================
# services/query_validator.py (Updated to fix result formatting)
# ============================================================================
import re
import sqlite3
from typing import Tuple, Optional, Any, Dict
from models.database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class QueryValidator:
    """Validates and sanitizes SQL queries"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def is_safe_query(self, query: str) -> bool:
        """Check if query is safe (read-only operations)"""
        # Remove comments and normalize whitespace
        clean_query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        clean_query = re.sub(r'/\*.*?\*/', '', clean_query, flags=re.DOTALL)
        clean_query = clean_query.strip().upper()
        
        # Allow only SELECT, WITH (for CTEs), and EXPLAIN
        dangerous_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
            'TRUNCATE', 'REPLACE', 'ATTACH', 'DETACH', 'PRAGMA'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in clean_query:
                return False
        
        return clean_query.startswith(('SELECT', 'WITH', 'EXPLAIN'))
    
    def validate_syntax(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validate SQL syntax without executing"""
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            return True, None
        except sqlite3.Error as e:
            return False, str(e)
    
    def execute_safe_query(self, query: str, limit: int = 100) -> Tuple[bool, Any]:
        """Execute query safely with error handling"""
        try:
            if not self.is_safe_query(query):
                return False, "Query contains unsafe operations"
            
            # Add LIMIT if not present and it's a SELECT
            if 'LIMIT' not in query.upper() and query.strip().upper().startswith('SELECT'):
                query = f"{query.rstrip(';')} LIMIT {limit}"
            
            logger.info(f"Executing query: {query}")
            
            cursor = self.db_manager.connection.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [description[0] for description in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries for JSON serialization
            data = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    # Handle different data types properly
                    value = row[i]
                    if value is None:
                        row_dict[column] = None
                    elif isinstance(value, (int, float, str)):
                        row_dict[column] = value
                    else:
                        # Convert other types to string
                        row_dict[column] = str(value)
                data.append(row_dict)
            
            result = {
                'columns': columns,
                'data': data,
                'row_count': len(data),
                'query': query
            }
            
            logger.info(f"Query executed successfully, returned {len(data)} rows")
            return True, result
            
        except sqlite3.Error as e:
            logger.error(f"SQL Error: {e}")
            return False, f"SQL Error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False, f"Unexpected error: {str(e)}"

