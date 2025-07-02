

# services/secure_text_to_sql_service.py
"""
Secure text-to-SQL service using mock sample data
"""
import re
from typing import Dict, Any
from models.database import DatabaseManager
from models.secure_schema_inspector import SecureSchemaInspector
from services.query_validator import QueryValidator
from services.prompt_generator import PromptGenerator
from services.openai_service import OpenAIService
import logging

logger = logging.getLogger(__name__)

class SecureTextToSQLService:
    """Secure text-to-SQL service that uses mock sample data"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.schema_inspector = SecureSchemaInspector(db_manager)
        self.validator = QueryValidator(db_manager)
        self.openai_service = OpenAIService()
        self.db_context = None
        self.prompt_generator = None
        self._initialize_context()
    
    def _initialize_context(self):
        """Initialize database context with secure schema inspector"""
        self.db_context = self.schema_inspector.get_database_context()
        self.prompt_generator = PromptGenerator(self.db_context)
        
        # Log security status
        if self.db_context.get('missing_mock_tables'):
            logger.warning(f"Security Alert: Some tables missing mock data: {self.db_context['missing_mock_tables']}")
        else:
            logger.info("Security: All tables have corresponding mock sample data")
    
    def process_question(self, user_question: str) -> Dict[str, Any]:
        """Process question using secure mock sample data"""
        try:
            logger.info(f"Processing question securely: {user_question}")
            
            # Test OpenAI connection
            if not self.openai_service.test_connection():
                return {
                    'success': False,
                    'error': 'OpenAI API is not accessible. Please check your API key.',
                    'question': user_question
                }
            
            # Generate prompt (using mock sample data)
            prompt = self.prompt_generator.create_text_to_sql_prompt(user_question)
            
            # Add security note to prompt
            secure_prompt = f"""{prompt}

SECURITY NOTE: The sample data shown above is mock/test data for context only. 
Generate queries against the actual table names (without _sample suffix).
"""
            
            # Generate SQL
            generated_sql = self.openai_service.generate_sql(secure_prompt)
            if generated_sql is None:
                return {
                    'success': False,
                    'error': 'Failed to generate SQL from OpenAI',
                    'question': user_question
                }
            
            # Clean and validate
            sql_query = self.clean_generated_sql(generated_sql)
            
            # Security check: ensure no _sample tables in final query
            if '_sample' in sql_query.lower():
                sql_query = re.sub(r'\b\w+_sample\b', lambda m: m.group().replace('_sample', ''), sql_query)
                logger.info("Removed _sample suffixes from generated query")
            
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
                    'suggestion': 'Try rephrasing your question or being more specific.'
                }
            
            # Execute query on REAL tables
            success, result = self.validator.execute_safe_query(sql_query)
            
            if success:
                return {
                    'success': True,
                    'query': sql_query,
                    'result': result,
                    'question': user_question,
                    'security_info': {
                        'mode': 'secure_mock_samples',
                        'real_data_protected': True,
                        'sample_data_source': 'mock_tables'
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
            logger.error(f"Error processing question securely: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Processing error: {str(e)}",
                'question': user_question
            }
    
    def clean_generated_sql(self, generated_sql: str) -> str:
        """Clean generated SQL and ensure no sample table references"""
        sql = generated_sql.strip()
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        
        # Remove any _sample references the AI might have included
        sql = re.sub(r'\b(\w+)_sample\b', r'\1', sql)
        
        return sql.strip()
    
    def attempt_query_fix(self, sql_query: str, error_msg: str) -> str:
        """Attempt to fix common SQL errors"""
        fixed_query = sql_query
        
        # Fix table name issues
        if "no such table" in error_msg.lower():
            for table_name in self.db_context['tables']:
                if table_name.lower() in sql_query.lower():
                    fixed_query = re.sub(
                        rf'\b{re.escape(table_name)}\b', 
                        table_name, 
                        fixed_query, 
                        flags=re.IGNORECASE
                    )
        
        return fixed_query
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information with security status"""
        return {
            'total_tables': len(self.db_context['tables']),
            'tables': self.db_context['tables'],
            'security_mode': 'mock_samples',
            'missing_mock_tables': self.db_context.get('missing_mock_tables', []),
            'openai_status': self.openai_service.test_connection(),
            'data_protection': 'PCI/MNPI compliant - using mock sample data'
        }
    
    def generate_mock_setup_script(self) -> str:
        """Generate SQL script to create all missing mock tables"""
        missing_tables = self.db_context.get('missing_mock_tables', [])
        
        if not missing_tables:
            return "-- All mock tables already exist!"
        
        script_parts = ["-- Mock Table Setup Script", "-- Generated for PCI/MNPI compliance", ""]
        
        for table_name in missing_tables:
            template = self.schema_inspector.create_mock_table_template(table_name)
            script_parts.append(template)
            script_parts.append("")
        
        return "\n".join(script_parts)
    
    def refresh_context(self):
        """Refresh database context"""
        self._initialize_context()

# Example mock data setup for your tables
MOCK_DATA_EXAMPLES = {
    'users_sample': """
INSERT INTO users_sample VALUES 
(1, 'john_demo', 'john.demo@example.com', 'John', 'Demo', '2023-01-15', 1, 'customer'),
(2, 'jane_test', 'jane.test@example.com', 'Jane', 'Test', '2023-06-20', 1, 'customer'),
(3, 'admin_mock', 'admin.mock@example.com', 'Admin', 'User', '2022-12-01', 1, 'admin');
""",
    
    'transactions_sample': """
INSERT INTO transactions_sample VALUES 
(1, 1, '2024-01-15 10:30:00', 'purchase', 299.99, 'completed', 'DEMO_TXN_001'),
(2, 2, '2024-01-16 14:20:00', 'refund', -50.00, 'completed', 'DEMO_TXN_002'),
(3, 1, '2024-01-17 09:15:00', 'purchase', 1299.99, 'pending', 'DEMO_TXN_003');
""",
    
    'accounts_sample': """
INSERT INTO accounts_sample VALUES 
(1, 1, 'checking', 'DEMO123456789', 5000.00, 'active', '2023-01-15'),
(2, 2, 'savings', 'DEMO987654321', 15000.00, 'active', '2023-06-20'),
(3, 1, 'credit', 'DEMO555666777', -1200.00, 'active', '2023-03-10');
"""
}