"""
Secure text-to-SQL service using mock sample data for PCI/MNPI compliance
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
    """Secure text-to-SQL service that uses mock sample data for AI context"""
    
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
        try:
            self.db_context = self.schema_inspector.get_database_context()
            self.prompt_generator = PromptGenerator(self.db_context)
            
            # Log security status
            missing_mock_tables = self.db_context.get('missing_mock_tables', [])
            if missing_mock_tables:
                logger.warning(f"Security Alert: Some tables missing mock data: {missing_mock_tables}")
                logger.warning("Consider creating mock tables for complete PCI/MNPI compliance")
            else:
                logger.info("Security: All tables have corresponding mock sample data")
                
            logger.info(f"Initialized secure context with {len(self.db_context['tables'])} tables")
            
        except Exception as e:
            logger.error(f"Failed to initialize secure context: {e}")
            raise
    
    def process_question(self, user_question: str) -> Dict[str, Any]:
        """Process question using secure mock sample data"""
        try:
            logger.info(f"Processing question securely: {user_question}")
            
            # Validate input
            if not user_question or not user_question.strip():
                return {
                    'success': False,
                    'error': 'Empty question provided',
                    'question': user_question
                }
            
            # Test OpenAI connection first
            if not self.test_openai_connection():
                return {
                    'success': False,
                    'error': 'OpenAI API is not accessible. Please check your API key and internet connection.',
                    'question': user_question,
                    'suggestion': 'Verify your OPENAI_API_KEY in the .env file'
                }
            
            # Generate prompt using mock sample data
            prompt = self.create_secure_prompt(user_question)
            logger.debug("Generated secure prompt for OpenAI")
            
            # Generate SQL using OpenAI
            generated_sql = self.openai_service.generate_sql(prompt)
            if generated_sql is None:
                return {
                    'success': False,
                    'error': 'Failed to generate SQL from OpenAI. API may be temporarily unavailable.',
                    'question': user_question,
                    'suggestion': 'Try rephrasing your question or check OpenAI service status'
                }
            
            logger.info(f"OpenAI generated SQL: {generated_sql[:100]}...")
            
            # Clean and secure the generated SQL
            sql_query = self.clean_and_secure_sql(generated_sql)
            logger.info(f"Cleaned SQL: {sql_query}")
            
            # Validate SQL syntax
            is_valid, error_msg = self.validator.validate_syntax(sql_query)
            if not is_valid:
                logger.warning(f"SQL validation failed: {error_msg}")
                # Try to fix common issues
                sql_query = self.attempt_query_fix(sql_query, error_msg)
                is_valid, error_msg = self.validator.validate_syntax(sql_query)
                
                if is_valid:
                    logger.info("Successfully fixed SQL query")
                else:
                    logger.error(f"Could not fix SQL query: {error_msg}")
            
            if not is_valid:
                return {
                    'success': False,
                    'error': f"Invalid SQL generated: {error_msg}",
                    'query': sql_query,
                    'question': user_question,
                    'suggestion': 'Try rephrasing your question or being more specific about table names.'
                }
            
            # Execute query on REAL tables (not sample tables)
            logger.info("Executing validated SQL query on real tables")
            success, result = self.validator.execute_safe_query(sql_query)
            
            if success:
                logger.info(f"Query executed successfully, returned {result['row_count']} rows")
                return {
                    'success': True,
                    'query': sql_query,
                    'result': result,
                    'question': user_question,
                    'security_info': {
                        'mode': 'secure_mock_samples',
                        'real_data_protected': True,
                        'sample_data_source': 'mock_tables',
                        'compliance': 'PCI/MNPI'
                    }
                }
            else:
                logger.error(f"Query execution failed: {result}")
                return {
                    'success': False,
                    'error': result,  # result contains the error message
                    'query': sql_query,
                    'question': user_question,
                    'suggestion': 'The SQL was valid but failed to execute. Check if the referenced tables and columns exist.'
                }
                
        except Exception as e:
            logger.error(f"Error processing question securely: {e}", exc_info=True)
            return {
                'success': False,
                'error': f"Processing error: {str(e)}",
                'question': user_question,
                'suggestion': 'Please try again or contact support if the issue persists.'
            }
    
    def create_secure_prompt(self, user_question: str) -> str:
        """Create a secure prompt using mock sample data"""
        
        # Generate base prompt with mock sample data
        base_prompt = self.prompt_generator.create_text_to_sql_prompt(user_question)
        
        # Add security instructions
        secure_prompt = f"""{base_prompt}

IMPORTANT SECURITY NOTES:
- The sample data shown above is mock/test data for context only
- Generate queries against the actual table names (without _sample suffix)
- Do not reference any _sample tables in your SQL output
- Focus on the table structure and data patterns, not the actual sample values

Remember: Query the real tables, not the sample tables!

Question: {user_question}

SQL Query:"""
        
        return secure_prompt
    
    def clean_and_secure_sql(self, generated_sql: str) -> str:
        """Clean generated SQL and ensure no sample table references"""
        
        # Basic cleaning
        sql = generated_sql.strip()
        
        # Remove markdown code blocks
        sql = re.sub(r'```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'```\s*', '', sql)
        
        # Remove explanatory text that AI might add
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
        
        sql = ' '.join(sql_lines) if sql_lines else sql
        
        # Security: Remove any _sample references the AI might have included
        sql = re.sub(r'\b(\w+)_sample\b', r'\1', sql, flags=re.IGNORECASE)
        
        # Remove any remaining explanatory text
        sql = re.sub(r'^.*?(?=SELECT|WITH|EXPLAIN)', '', sql, flags=re.IGNORECASE | re.DOTALL)
        
        # Ensure single line formatting
        sql = ' '.join(sql.split())
        
        # Add semicolon if missing
        if not sql.rstrip().endswith(';'):
            sql = sql.rstrip() + ';'
        
        return sql.strip()
    
    def attempt_query_fix(self, sql_query: str, error_msg: str) -> str:
        """Attempt to fix common SQL errors"""
        
        fixed_query = sql_query
        
        # Fix table name case issues
        if "no such table" in error_msg.lower():
            for table_name in self.db_context['tables']:
                # Replace case-insensitive table name references
                pattern = rf'\b{re.escape(table_name)}\b'
                fixed_query = re.sub(pattern, table_name, fixed_query, flags=re.IGNORECASE)
        
        # Fix column name issues
        if "no such column" in error_msg.lower():
            # Extract column name from error message
            column_match = re.search(r'no such column: (\w+)', error_msg, re.IGNORECASE)
            if column_match:
                error_column = column_match.group(1)
                # Try to find similar column names
                for table_name, schema in self.db_context['schemas'].items():
                    for column in schema.columns:
                        if column['name'].lower() == error_column.lower():
                            fixed_query = re.sub(
                                rf'\b{re.escape(error_column)}\b',
                                column['name'],
                                fixed_query,
                                flags=re.IGNORECASE
                            )
                            break
        
        # Remove any remaining _sample references
        fixed_query = re.sub(r'\b(\w+)_sample\b', r'\1', fixed_query, flags=re.IGNORECASE)
        
        logger.info(f"Attempted to fix SQL: {sql_query} -> {fixed_query}")
        return fixed_query
    
    def test_openai_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            return self.openai_service.test_connection()
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information with security status"""
        
        try:
            missing_mock_tables = self.db_context.get('missing_mock_tables', [])
            
            return {
                'total_tables': len(self.db_context['tables']),
                'tables': self.db_context['tables'],
                'security_mode': 'mock_samples',
                'missing_mock_tables': missing_mock_tables,
                'compliance_status': 'PCI/MNPI Compliant' if not missing_mock_tables else 'Partial Compliance',
                'openai_status': self.test_openai_connection(),
                'data_protection': 'Real data protected - using mock sample data for AI context',
                'sample_tables_found': len(self.db_context['tables']) - len(missing_mock_tables),
                'schemas_loaded': len(self.db_context['schemas'])
            }
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {
                'error': f"Could not retrieve database info: {str(e)}",
                'security_mode': 'unknown',
                'openai_status': False
            }
    
    def generate_mock_setup_script(self) -> str:
        """Generate SQL script to create all missing mock tables"""
        
        try:
            missing_tables = self.db_context.get('missing_mock_tables', [])
            
            if not missing_tables:
                return "-- All mock tables already exist! Your database is fully PCI/MNPI compliant."
            
            script_parts = [
                "-- Mock Table Setup Script",
                "-- Generated for PCI/MNPI compliance",
                f"-- Missing tables: {', '.join(missing_tables)}",
                ""
            ]
            
            for table_name in missing_tables:
                try:
                    template = self.schema_inspector.create_mock_table_template(table_name)
                    script_parts.append(template)
                    script_parts.append("")
                except Exception as e:
                    script_parts.append(f"-- Error generating template for {table_name}: {e}")
                    script_parts.append("")
            
            return "\n".join(script_parts)
            
        except Exception as e:
            logger.error(f"Error generating mock setup script: {e}")
            return f"-- Error generating script: {str(e)}"
    
    def validate_security_compliance(self) -> Dict[str, Any]:
        """Validate current security compliance status"""
        
        try:
            missing_mock_tables = self.db_context.get('missing_mock_tables', [])
            total_tables = len(self.db_context['tables'])
            compliant_tables = total_tables - len(missing_mock_tables)
            
            compliance_percentage = (compliant_tables / total_tables * 100) if total_tables > 0 else 0
            
            return {
                'is_fully_compliant': len(missing_mock_tables) == 0,
                'compliance_percentage': round(compliance_percentage, 1),
                'total_tables': total_tables,
                'compliant_tables': compliant_tables,
                'missing_mock_tables': missing_mock_tables,
                'recommendations': self._get_compliance_recommendations(missing_mock_tables),
                'security_level': self._get_security_level(compliance_percentage)
            }
            
        except Exception as e:
            logger.error(f"Error validating security compliance: {e}")
            return {
                'is_fully_compliant': False,
                'error': str(e),
                'security_level': 'unknown'
            }
    
    def _get_compliance_recommendations(self, missing_tables: list) -> list:
        """Get recommendations for improving compliance"""
        
        recommendations = []
        
        if missing_tables:
            recommendations.extend([
                f"Create mock sample tables for: {', '.join(missing_tables)}",
                "Use the generate_mock_setup_script() method to get SQL templates",
                "Ensure mock data is realistic but completely fictional",
                "Test AI query generation after adding mock tables"
            ])
        else:
            recommendations.extend([
                "✅ Full PCI/MNPI compliance achieved",
                "Regularly audit mock data to ensure it remains fictional",
                "Monitor query logs for any potential data exposure",
                "Keep mock data updated when real schema changes"
            ])
        
        return recommendations
    
    def _get_security_level(self, compliance_percentage: float) -> str:
        """Get security level based on compliance percentage"""
        
        if compliance_percentage >= 100:
            return "FULLY_COMPLIANT"
        elif compliance_percentage >= 80:
            return "MOSTLY_COMPLIANT"
        elif compliance_percentage >= 50:
            return "PARTIALLY_COMPLIANT"
        else:
            return "NON_COMPLIANT"
    
    def refresh_context(self):
        """Refresh database context (call after schema changes)"""
        try:
            logger.info("Refreshing secure database context...")
            self._initialize_context()
            logger.info("Context refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh context: {e}")
            raise
    
    def get_table_sample_status(self) -> Dict[str, bool]:
        """Get the mock sample table status for each real table"""
        
        try:
            status = {}
            for table_name in self.db_context['tables']:
                has_mock = self.schema_inspector.check_mock_table_exists(table_name)
                status[table_name] = has_mock
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting table sample status: {e}")
            return {}
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get overall service health status"""
        
        try:
            compliance = self.validate_security_compliance()
            
            health = {
                'status': 'healthy',
                'timestamp': str(logger.handlers[0].formatter.formatTime(logger.makeRecord(
                    '', 0, '', 0, '', (), None
                )) if logger.handlers else 'unknown'),
                'database_connected': True,
                'openai_connected': self.test_openai_connection(),
                'security_compliant': compliance['is_fully_compliant'],
                'total_tables': compliance['total_tables'],
                'missing_mock_tables': len(compliance.get('missing_mock_tables', [])),
                'service_version': '1.0.0',
                'security_mode': 'mock_samples'
            }
            
            # Determine overall health
            if not health['openai_connected']:
                health['status'] = 'degraded'
                health['issues'] = ['OpenAI API not accessible']
            elif not health['security_compliant']:
                health['status'] = 'warning'
                health['issues'] = ['Some tables missing mock data']
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting service health: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': 'unknown'
            }