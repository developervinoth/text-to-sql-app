# Flask Text-to-SQL Application

A modular Flask-based application that converts natural language questions into SQL queries and executes them against a SQLite database.

## Features

- **Natural Language to SQL**: Convert human questions into SQL queries
- **Modular Architecture**: Clean separation of concerns across multiple modules
- **Schema Introspection**: Automatically discovers database structure
- **Column Descriptions**: Rich metadata for better query generation
- **Query Validation**: Ensures safe, read-only operations
- **Web Interface**: Modern, responsive UI for easy interaction
- **Sample Database**: Includes complete e-commerce example with metadata

## Project Structure

```
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── run.py                      # Application entry point
├── setup_database.py           # Sample database creation script
├── requirements.txt            # Python dependencies
├── models/
│   ├── database.py            # Database connection management
│   └── schema_inspector.py    # Database schema introspection
├── services/
│   ├── query_validator.py     # SQL query validation and execution
│   ├── prompt_generator.py    # AI prompt generation
│   └── text_to_sql_service.py # Main text-to-SQL service
└── templates/
    └── index.html             # Web interface template
```

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install Flask sqlite3
   ```

2. **Run the Application**:
   ```bash
   python run.py
   ```

3. **Access the Interface**:
   Open http://localhost:5000 in your browser

4. **Try Sample Questions**:
   - "Show me all users who joined this year"
   - "What are the top 5 most expensive products?"
   - "How many orders were placed last month?"

## Database Schema

The sample database includes:

### Business Tables
- **users**: Customer and admin accounts
- **categories**: Product categories (hierarchical)
- **products**: Product catalog with pricing
- **orders**: Customer orders with status tracking
- **order_items**: Individual order line items

### Metadata Tables
- **table_descriptions**: Business descriptions for each table
- **column_descriptions**: Detailed column metadata including:
  - Technical description
  - Business meaning
  - Example values

## Integration Point

Replace the placeholder function in `services/text_to_sql_service.py`:

```python
def generate_sql_response(self, prompt: str) -> str:
    """
    Replace this with your actual text generation function
    """
    # Your existing function call here
    return your_existing_function(prompt)
```

## API Endpoints

- `POST /api/query`: Process natural language questions
- `GET /api/database-info`: Get database schema information  
- `POST /api/refresh-schema`: Refresh cached schema data

## Sample Questions

The application works well with questions like:
- "Show me all active users"
- "Find the most popular products"
- "What's the total revenue by category?"
- "Which customers have never placed an order?"
- "Show products that are out of stock"

## Customization

### Adding Your Own Database

1. Update `DATABASE_PATH` in `config.py`
2. Create metadata tables using the schema in `setup_database.py`
3. Add your table and column descriptions
4. Run `/api/refresh-schema` to update the cache

### Modifying the UI

Edit `templates/index.html` to customize the interface, add new features, or change the styling.

## Safety Features

- **Read-only Operations**: Only SELECT queries allowed
- **Query Validation**: Syntax checking before execution
- **Result Limiting**: Automatic LIMIT clauses for large datasets
- **Error Handling**: Graceful handling of invalid queries
- **SQL Injection Protection**: Parameterized queries and validation


### Fix 2.0
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