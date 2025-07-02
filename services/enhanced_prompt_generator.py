from typing import Dict, Any
from services.smart_schema_service import SmartSchemaService

class EnhancedPromptGenerator:
    """Generates optimized prompts for large databases"""
    
    def __init__(self, smart_schema_service: SmartSchemaService):
        self.smart_schema_service = smart_schema_service
    
    def create_focused_schema_prompt(self, user_question: str, max_tables: int = 10) -> str:
        """Create a focused schema description with only relevant tables"""
        
        # Get contextual schema
        context = self.smart_schema_service.get_contextual_schema(user_question, max_tables)
        
        prompt_parts = []
        prompt_parts.append("Database Schema Information:")
        prompt_parts.append("=" * 50)
        
        # Add database overview
        if context['showing_tables'] < context['total_tables']:
            prompt_parts.append(f"Note: Showing {context['showing_tables']} most relevant tables out of {context['total_tables']} total tables.\n")
        
        for table_name, schema in context['schemas'].items():
            prompt_parts.append(f"\nTable: {table_name}")
            if schema.description:
                prompt_parts.append(f"Description: {schema.description}")
            prompt_parts.append("-" * 30)
            
            # Column information with descriptions
            prompt_parts.append("Columns:")
            column_descriptions = {
                cd.column_name: cd for cd in context['column_descriptions'].get(table_name, [])
            }
            
            for col in schema.columns:
                pk_indicator = " (PRIMARY KEY)" if col['primary_key'] else ""
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                col_line = f"  - {col['name']}: {col['type']} {nullable}{pk_indicator}"
                
                # Add column description if available
                if col['name'] in column_descriptions:
                    cd = column_descriptions[col['name']]
                    col_line += f"\n    Description: {cd.description}"
                    if cd.business_meaning:
                        col_line += f"\n    Business Meaning: {cd.business_meaning}"
                
                prompt_parts.append(col_line)
            
            # Sample data (limited for large schemas)
            if schema.sample_data:
                prompt_parts.append("Sample Data:")
                for i, row in enumerate(schema.sample_data[:2], 1):  # Only 2 sample rows
                    prompt_parts.append(f"  Row {i}: {dict(row)}")
        
        return "\n".join(prompt_parts)
    
    def create_text_to_sql_prompt(self, user_question: str, max_tables: int = 10) -> str:
        """Create complete prompt for text-to-SQL generation with intelligent table selection"""
        
        schema_info = self.create_focused_schema_prompt(user_question, max_tables)
        
        prompt = f"""You are an expert SQL query generator. Convert the natural language question into a valid SQLite query.

        {schema_info}

        Important Notes:
        - Tables are independent (no foreign key relationships)
        - Focus on the tables most relevant to the question
        - If you need to join data from multiple tables, you cannot use foreign keys
        - Use WHERE clauses to filter data appropriately
        - Consider using UNION if combining data from similar tables

        Rules:
        1. Generate ONLY the SQL query, no explanations
        2. Use proper SQLite syntax
        3. Handle the fact that tables are not related
        4. Include LIMIT clause for potentially large results (max 100 rows)
        5. Use table and column descriptions to understand business context
        6. Be case-insensitive in your matching

        Question: {user_question}

        SQL Query:"""
        
        return prompt