import re
from typing import Dict, Any
from models.database import DatabaseManager
from services.query_validator import QueryValidator
from services.openai_service import OpenAIService
from services.smart_schema_service import SmartSchemaService
from services.enhanced_prompt_generator import EnhancedPromptGenerator
import logging

logger = logging.getLogger(__name__)

class EnhancedTextToSQLService:
    """Enhanced service for large, non-relational databases"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.validator = QueryValidator(db_manager)
        self.openai_service = OpenAIService()
        self.smart_schema_service = SmartSchemaService(db_manager)
        self.prompt_generator = EnhancedPromptGenerator(self.smart_schema_service)
    
    def process_question(self, user_question: str, max_tables: int = 10) -> Dict[str, Any]:
        """Process question with intelligent table selection"""
        try:
            logger.info(f"Processing question: {user_question}")
            
            # Test OpenAI connection
            if not self.openai_service.test_connection():
                return {
                    'success': False,
                    'error': 'OpenAI API is not accessible. Please check your API key.',
                    'question': user_question
                }
            
            # Generate focused prompt
            prompt = self.prompt_generator.create_text_to_sql_prompt(user_question, max_tables)
            logger.info(f"Generated focused prompt with {max_tables} max tables")
            
            # Generate SQL
            generated_sql = self.openai_service.generate_sql(prompt)
            if generated_sql is None:
                return {
                    'success': False,
                    'error': 'Failed to generate SQL from OpenAI',
                    'question': user_question
                }
            
            # Clean and validate
            sql_query = self.clean_generated_sql(generated_sql)
            is_valid, error_msg = self.validator.validate_syntax(sql_query)
            
            if not is_valid:
                sql_query = self.attempt_query_fix(sql_query, error_msg)
                is_valid, error_msg = self.validator.validate_syntax(sql_query)
            
            if not is_valid:
                return {
                    'success': False,
                    'error': f"Invalid SQL: {error_msg}",
                    'query': sql_query,
                    'question': user_question,
                    'suggestion': 'Try being more specific about which table contains the data you need.'
                }
            
            # Execute query
            success, result = self.validator.execute_safe_query(sql_query)
            
            if success:
                # Add metadata about table selection
                relevant_tables = self.smart_schema_service.get_relevant_tables(user_question, max_tables)
                result['relevant_tables'] = relevant_tables
                result['total_tables_in_db'] = len(self.smart_schema_service.full_context['tables'])
                
                return {
                    'success': True,
                    'query': sql_query,
                    'result': result,
                    'question': user_question,
                    'metadata': {
                        'tables_considered': len(relevant_tables),
                        'total_tables': len(self.smart_schema_service.full_context['tables']),
                        'relevant_tables': relevant_tables
                    }
                }
            else:
                return {
                    'success': False,
                    'error': result,
                    'query': sql_query,
                    'question': user_question
                }
                
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Processing error: {str(e)}",
                'question': user_question
            }
    
    def clean_generated_sql(self, generated_sql: str) -> str:
        """Clean generated SQL"""
        sql = generated_sql.strip()
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        return sql.strip()
    
    def attempt_query_fix(self, sql_query: str, error_msg: str) -> str:
        """Attempt to fix common errors"""
        fixed_query = sql_query
        
        # Fix table name issues
        if "no such table" in error_msg.lower():
            all_tables = self.smart_schema_service.full_context['tables']
            for table_name in all_tables:
                if table_name.lower() in sql_query.lower():
                    fixed_query = re.sub(
                        rf'\b{re.escape(table_name)}\b', 
                        table_name, 
                        fixed_query, 
                        flags=re.IGNORECASE
                    )
        
        return fixed_query
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get enhanced database information"""
        full_context = self.smart_schema_service.full_context
        return {
            'total_tables': len(full_context['tables']),
            'tables': full_context['tables'],
            'is_large_database': len(full_context['tables']) > 20,
            'uses_intelligent_selection': True,
            'openai_status': self.openai_service.test_connection()
        }