
import re
from typing import Dict, List, Any, Optional
from models.database import DatabaseManager
from models.schema_inspector import SchemaInspector
import logging

logger = logging.getLogger(__name__)

class SmartSchemaService:
    """Intelligent schema management for large databases"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.schema_inspector = SchemaInspector(db_manager)
        self.full_context = None
        self._initialize_context()
    
    def _initialize_context(self):
        """Initialize and cache full database context"""
        self.full_context = self.schema_inspector.get_database_context()
        logger.info(f"Loaded schema for {len(self.full_context['tables'])} tables")
    
    def get_relevant_tables(self, user_question: str, max_tables: int = 10) -> List[str]:
        """
        Intelligently select relevant tables based on user question
        
        Args:
            user_question: The user's natural language question
            max_tables: Maximum number of tables to include in context
            
        Returns:
            List of relevant table names
        """
        question_lower = user_question.lower()
        all_tables = self.full_context['tables']
        
        # Score tables based on relevance
        table_scores = {}
        
        for table_name in all_tables:
            score = 0
            table_lower = table_name.lower()
            schema = self.full_context['schemas'][table_name]
            
            # Direct table name mention
            if table_lower in question_lower:
                score += 100
            
            # Partial table name match
            if any(part in question_lower for part in table_lower.split('_')):
                score += 50
            
            # Column name mentions
            for column in schema.columns:
                col_name = column['name'].lower()
                if col_name in question_lower:
                    score += 30
                
                # Partial column name match
                if any(part in question_lower for part in col_name.split('_')):
                    score += 15
            
            # Table description keywords
            if schema.description:
                desc_words = schema.description.lower().split()
                question_words = question_lower.split()
                common_words = set(desc_words) & set(question_words)
                score += len(common_words) * 10
            
            # Column descriptions
            column_descs = self.full_context['column_descriptions'].get(table_name, [])
            for col_desc in column_descs:
                if any(word in col_desc.description.lower() for word in question_lower.split()):
                    score += 5
            
            table_scores[table_name] = score
        
        # Sort by score and return top tables
        sorted_tables = sorted(table_scores.items(), key=lambda x: x[1], reverse=True)
        relevant_tables = [table for table, score in sorted_tables[:max_tables] if score > 0]
        
        # If no relevant tables found, include some core tables
        if not relevant_tables:
            relevant_tables = all_tables[:max_tables]
        
        logger.info(f"Selected {len(relevant_tables)} relevant tables: {relevant_tables}")
        return relevant_tables
    
    def get_contextual_schema(self, user_question: str, max_tables: int = 10) -> Dict[str, Any]:
        """
        Get schema context with only relevant tables
        
        Args:
            user_question: The user's natural language question
            max_tables: Maximum number of tables to include
            
        Returns:
            Filtered database context
        """
        relevant_tables = self.get_relevant_tables(user_question, max_tables)
        
        filtered_context = {
            'tables': relevant_tables,
            'schemas': {table: self.full_context['schemas'][table] for table in relevant_tables},
            'column_descriptions': {
                table: self.full_context['column_descriptions'].get(table, []) 
                for table in relevant_tables
            },
            'total_tables': len(self.full_context['tables']),
            'showing_tables': len(relevant_tables)
        }
        
        return filtered_context