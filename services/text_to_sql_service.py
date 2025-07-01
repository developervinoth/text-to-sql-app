# ============================================================================
# services/text_to_sql_service.py (Updated with better error handling)
# ============================================================================
import re
from typing import Dict, Any
from models.database import DatabaseManager
from models.schema_inspector import SchemaInspector
from services.query_validator import QueryValidator
from services.prompt_generator import PromptGenerator
from services.openai_service import OpenAIService
import logging

logger = logging.getLogger(__name__)

class TextToSQLService:
    """Main service class for text-to-SQL conversion using OpenAI"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.schema_inspector = SchemaInspector(db_manager)
        self.validator = QueryValidator(db_manager)
        self.openai_service = OpenAIService()
        self.db_context = None
        self.prompt_generator = None
        self._initialize_context()
    
    def _initialize_context(self):
        """Initialize database context and prompt generator"""
        self.db_context = self.schema_inspector.get_database_context()
        self.prompt_generator = PromptGenerator(self.db_context)
    
    def generate_sql_response(self, prompt: str) -> str:
        """
        Generate SQL response using OpenAI API
        
        Args:
            prompt (str): The text-to-SQL prompt with schema information
            
        Returns:
            str: Generated SQL query
        """
        sql_query = self.openai_service.generate_sql(prompt)
        
        if sql_query is None:
            # Fallback to a simple query if OpenAI fails
            logger.warning("OpenAI API failed, using fallback query")
            return "SELECT 'OpenAI API unavailable. Please check your API key and try again.' as error_message;"
        
        return sql_query
    
    def process_question(self, user_question: str) -> Dict[str, Any]:
        """Process natural language question and return SQL query with results"""
        try:
            logger.info(f"Processing question: {user_question}")
            
            # Test OpenAI connection first
            if not self.test_openai_connection():
                return {
                    'success': False,
                    'error': 'OpenAI API is not accessible. Please check your API key and internet connection.',
                    'question': user_question
                }
            
            # Generate prompt
            prompt = self.prompt_generator.create_text_to_sql_prompt(user_question)
            logger.info("Generated prompt for OpenAI")
            
            # Generate SQL query using OpenAI
            generated_sql = self.generate_sql_response(prompt)
            logger.info(f"OpenAI generated SQL: {generated_sql}")
            
            # Clean up the generated SQL
            sql_query = self.clean_generated_sql(generated_sql)
            logger.info(f"Cleaned SQL: {sql_query}")
            
            # Validate the query
            is_valid, error_msg = self.validator.validate_syntax(sql_query)
            if not is_valid:
                logger.warning(f"SQL validation failed: {error_msg}")
                # Try to fix common issues
                sql_query = self.attempt_query_fix(sql_query, error_msg)
                is_valid, error_msg = self.validator.validate_syntax(sql_query)
            
            if not is_valid:
                return {
                    'success': False,
                    'error': f"Invalid SQL generated: {error_msg}",
                    'query': sql_query,
                    'question': user_question,
                    'suggestion': 'Try rephrasing your question or being more specific.'
                }
            
            # Execute the query
            logger.info("Executing validated SQL query")
            success, result = self.validator.execute_safe_query(sql_query)
            
            if success:
                logger.info(f"Query executed successfully, returned {result['row_count']} rows")
                return {
                    'success': True,
                    'query': sql_query,
                    'result': result,
                    'question': user_question,
                    'prompt_used': prompt
                }
            else:
                logger.error(f"Query execution failed: {result}")
                return {
                    'success': False,
                    'error': result,  # result contains the error message
                    'query': sql_query,
                    'question': user_question,
                    'suggestion': 'The query was valid but failed to execute. Try a different approach.'
                }
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Processing error: {str(e)}",
                'question': user_question
            }
    
    def test_openai_connection(self) -> bool:
        """Test OpenAI API connection"""
        return self.openai_service.test_connection()
    
    def clean_generated_sql(self, generated_sql: str) -> str:
        """Clean and normalize generated SQL"""
        sql = generated_sql.strip()
        
        # Remove markdown code blocks
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        
        # Remove explanatory text before/after SQL
        lines = sql.split('\n')
        sql_lines = []
        in_sql = False
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith(('SELECT', 'WITH', 'EXPLAIN')):
                in_sql = True
                sql_lines.append(line)
            elif in_sql and line and not line.startswith(('--', 'Note:', 'Explanation:', 'Here', 'This')):
                sql_lines.append(line)
            elif in_sql and line.endswith(';'):
                sql_lines.append(line)
                break
        
        result = ' '.join(sql_lines) if sql_lines else sql
        
        # Remove any remaining explanatory text
        result = re.sub(r'^.*?(?=SELECT|WITH|EXPLAIN)', '', result, flags=re.IGNORECASE | re.DOTALL)
        
        return result.strip()
    
    def attempt_query_fix(self, sql_query: str, error_msg: str) -> str:
        """Attempt to fix common SQL errors"""
        fixed_query = sql_query
        
        # Fix table/column name issues
        if "no such table" in error_msg.lower():
            for table_name in self.db_context['tables']:
                if table_name.lower() in sql_query.lower():
                    fixed_query = re.sub(
                        rf'\b{re.escape(table_name)}\b', 
                        table_name, 
                        fixed_query, 
                        flags=re.IGNORECASE
                    )
        
        # Add missing semicolon
        if not fixed_query.rstrip().endswith(';'):
            fixed_query = fixed_query.rstrip() + ';'
        
        return fixed_query
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information for debugging"""
        return {
            'total_tables': len(self.db_context['tables']),
            'tables': self.db_context['tables'],
            'schemas': {
                name: {
                    'columns': len(schema.columns),
                    'sample_rows': len(schema.sample_data),
                    'foreign_keys': len(schema.foreign_keys),
                    'description': schema.description
                }
                for name, schema in self.db_context['schemas'].items()
            },
            'openai_status': self.test_openai_connection()
        }
    
    def refresh_context(self):
        """Refresh database context (call after schema changes)"""
        self._initialize_context()
