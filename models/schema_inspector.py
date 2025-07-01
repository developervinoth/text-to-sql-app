from typing import Dict, List
from .database import DatabaseManager, TableSchema, ColumnDescription

class SchemaInspector:
    """Handles database schema introspection and metadata extraction"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_all_tables(self) -> List[str]:
        """Get all table names from the database"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        rows = self.db_manager.execute_query(query)
        return [row['name'] for row in rows]
    
    def get_table_schema(self, table_name: str) -> TableSchema:
        """Get complete schema information for a table"""
        # Get column information
        query = f"PRAGMA table_info({table_name})"
        column_rows = self.db_manager.execute_query(query)
        
        columns = []
        for row in column_rows:
            columns.append({
                'name': row['name'],
                'type': row['type'],
                'nullable': not row['notnull'],
                'primary_key': bool(row['pk']),
                'default_value': row['dflt_value']
            })
        
        # Get foreign key information
        fk_query = f"PRAGMA foreign_key_list({table_name})"
        fk_rows = self.db_manager.execute_query(fk_query)
        
        foreign_keys = []
        for row in fk_rows:
            foreign_keys.append({
                'column': row['from'],
                'referenced_table': row['table'],
                'referenced_column': row['to']
            })
        
        # Get sample data (first 3 rows)
        sample_query = f"SELECT * FROM {table_name} LIMIT 3"
        sample_rows = self.db_manager.execute_query(sample_query)
        sample_data = [dict(row) for row in sample_rows]
        
        # Get table description if exists
        desc_query = """
        SELECT description FROM table_descriptions 
        WHERE table_name = ? 
        """
        try:
            desc_rows = self.db_manager.execute_query(desc_query, (table_name,))
            description = desc_rows[0]['description'] if desc_rows else ""
        except:
            description = ""
        
        return TableSchema(
            name=table_name,
            columns=columns,
            sample_data=sample_data,
            foreign_keys=foreign_keys,
            description=description
        )
    
    def get_column_descriptions(self, table_name: str = None) -> List[ColumnDescription]:
        """Get column descriptions from metadata table"""
        query = """
        SELECT table_name, column_name, description, business_meaning, data_examples
        FROM column_descriptions
        """
        params = ()
        
        if table_name:
            query += " WHERE table_name = ?"
            params = (table_name,)
        
        try:
            rows = self.db_manager.execute_query(query, params)
            return [
                ColumnDescription(
                    table_name=row['table_name'],
                    column_name=row['column_name'],
                    description=row['description'],
                    business_meaning=row['business_meaning'] or "",
                    data_examples=row['data_examples'] or ""
                )
                for row in rows
            ]
        except:
            return []
    
    def get_database_context(self) -> Dict[str, any]:
        """Get complete database context for prompt generation"""
        tables = self.get_all_tables()
        schemas = {}
        column_descriptions = {}
        
        for table in tables:
            schemas[table] = self.get_table_schema(table)
            column_descriptions[table] = self.get_column_descriptions(table)
        
        return {
            'tables': tables,
            'schemas': schemas,
            'column_descriptions': column_descriptions,
            'total_tables': len(tables)
        }