# services/smart_schema_service.py
"""
Enhanced schema service for handling large databases with many tables
"""

# services/enhanced_prompt_generator.py
"""
Enhanced prompt generator that handles large schemas intelligently
"""


# services/enhanced_text_to_sql_service.py
"""
Enhanced service that handles large databases and non-relational tables
"""


# Example usage and configuration
"""
For 100+ tables, configure the service with:

# In your app.py, replace the TextToSQLService with:
enhanced_service = EnhancedTextToSQLService(db_manager)

# Process questions with table limits:
result = enhanced_service.process_question(question, max_tables=15)

# The service will automatically:
1. Analyze the question to find relevant tables
2. Score tables based on name/column/description matches
3. Include only the most relevant tables in the prompt
4. Generate SQL focused on those tables
5. Provide metadata about table selection
"""