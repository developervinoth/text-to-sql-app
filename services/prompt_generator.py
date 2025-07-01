from typing import Dict, Any

class PromptGenerator:
    """Generates prompts for the text-to-SQL model"""
    
    def __init__(self, database_context: Dict[str, Any]):
        self.db_context = database_context
    
    def create_schema_prompt(self) -> str:
        """Create a detailed schema description for the prompt"""
        prompt_parts = []
        prompt_parts.append("Database Schema Information:")
        prompt_parts.append("=" * 50)
        
        for table_name, schema in self.db_context['schemas'].items():
            prompt_parts.append(f"\nTable: {table_name}")
            if schema.description:
                prompt_parts.append(f"Description: {schema.description}")
            prompt_parts.append("-" * 30)
            
            # Column information with descriptions
            prompt_parts.append("Columns:")
            column_descriptions = {
                cd.column_name: cd for cd in self.db_context['column_descriptions'].get(table_name, [])
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
                    if cd.data_examples:
                        col_line += f"\n    Examples: {cd.data_examples}"
                
                prompt_parts.append(col_line)
            
            # Foreign keys
            if schema.foreign_keys:
                prompt_parts.append("Foreign Keys:")
                for fk in schema.foreign_keys:
                    prompt_parts.append(f"  - {fk['column']} -> {fk['referenced_table']}.{fk['referenced_column']}")
            
            # Sample data
            if schema.sample_data:
                prompt_parts.append("Sample Data:")
                for i, row in enumerate(schema.sample_data, 1):
                    prompt_parts.append(f"  Row {i}: {dict(row)}")
        
        return "\n".join(prompt_parts)
    
    def create_text_to_sql_prompt(self, user_question: str) -> str:
        """Create complete prompt for text-to-SQL generation"""
        schema_info = self.create_schema_prompt()
        
        prompt = f"""You are an expert SQL query generator. Convert the natural language question into a valid SQLite query.

        {schema_info}

        Rules:
        1. Generate ONLY the SQL query, no explanations
        2. Use proper SQLite syntax
        3. Always include appropriate WHERE clauses when filtering
        4. Use JOINs when accessing multiple tables
        5. Include LIMIT clause for potentially large results (max 100 rows)
        6. Handle NULL values appropriately
        7. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
        8. Ensure the query will not fail - use proper error handling
        9. Use table and column descriptions to understand business context
        10. Be case-insensitive in your matching

        Question: {user_question}

        SQL Query:"""
        
        return prompt