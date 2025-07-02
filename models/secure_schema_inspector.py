# models/secure_schema_inspector.py
"""
Secure schema inspector that uses mock sample tables for PCI/MNPI compliance
"""
from typing import Dict, List
from .database import DatabaseManager, TableSchema, ColumnDescription
import logging

logger = logging.getLogger(__name__)

class SecureSchemaInspector:
    """Schema inspector that uses mock sample tables for data privacy"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.mock_suffix = "_sample"  # Configurable suffix for mock tables
    
    def get_all_tables(self) -> List[str]:
        """Get all non-sample table names from the database"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        rows = self.db_manager.execute_query(query)
        
        # Filter out sample tables and metadata tables
        all_tables = [row['name'] for row in rows]
        real_tables = [
            table for table in all_tables 
            if not table.endswith(self.mock_suffix) 
            and table not in ['table_descriptions', 'column_descriptions']
        ]
        
        logger.info(f"Found {len(real_tables)} real tables (excluding {len(all_tables) - len(real_tables)} sample/metadata tables)")
        return real_tables
    
    def get_mock_table_name(self, real_table_name: str) -> str:
        """Get the corresponding mock table name for a real table"""
        return f"{real_table_name}{self.mock_suffix}"
    
    def check_mock_table_exists(self, real_table_name: str) -> bool:
        """Check if a mock table exists for the given real table"""
        mock_table = self.get_mock_table_name(real_table_name)
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name = ?"
        rows = self.db_manager.execute_query(query, (mock_table,))
        return len(rows) > 0
    
    def get_table_schema(self, table_name: str) -> TableSchema:
        """Get complete schema information for a table using mock data"""
        
        # Get column information from the REAL table
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
        
        # Get foreign key information from the REAL table
        fk_query = f"PRAGMA foreign_key_list({table_name})"
        fk_rows = self.db_manager.execute_query(fk_query)
        
        foreign_keys = []
        for row in fk_rows:
            foreign_keys.append({
                'column': row['from'],
                'referenced_table': row['table'],
                'referenced_column': row['to']
            })
        
        # Get sample data from the MOCK table (or empty if doesn't exist)
        sample_data = []
        mock_table_name = self.get_mock_table_name(table_name)
        
        if self.check_mock_table_exists(table_name):
            try:
                sample_query = f"SELECT * FROM {mock_table_name} LIMIT 5"
                sample_rows = self.db_manager.execute_query(sample_query)
                sample_data = [dict(row) for row in sample_rows]
                logger.info(f"Loaded {len(sample_data)} mock sample rows from {mock_table_name}")
            except Exception as e:
                logger.warning(f"Could not load sample data from {mock_table_name}: {e}")
                sample_data = []
        else:
            logger.warning(f"Mock table {mock_table_name} not found - no sample data will be provided")
        
        # Get table description if exists
        desc_query = "SELECT description FROM table_descriptions WHERE table_name = ?"
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
        """Get complete database context using mock sample data"""
        tables = self.get_all_tables()
        schemas = {}
        column_descriptions = {}
        
        missing_mock_tables = []
        
        for table in tables:
            schemas[table] = self.get_table_schema(table)
            column_descriptions[table] = self.get_column_descriptions(table)
            
            # Track tables without mock data
            if not self.check_mock_table_exists(table):
                missing_mock_tables.append(table)
        
        if missing_mock_tables:
            logger.warning(f"Missing mock tables for: {missing_mock_tables}")
        
        return {
            'tables': tables,
            'schemas': schemas,
            'column_descriptions': column_descriptions,
            'total_tables': len(tables),
            'missing_mock_tables': missing_mock_tables,
            'security_mode': 'mock_samples'
        }
    
    def create_mock_table_template(self, real_table_name: str) -> str:
        """Generate SQL template for creating a mock table"""
        
        # Get the real table structure
        query = f"PRAGMA table_info({real_table_name})"
        try:
            column_rows = self.db_manager.execute_query(query)
        except:
            return f"-- Error: Could not access table {real_table_name}"
        
        mock_table_name = self.get_mock_table_name(real_table_name)
        
        # Generate CREATE TABLE statement
        columns = []
        for row in column_rows:
            col_def = f"{row['name']} {row['type']}"
            if row['notnull']:
                col_def += " NOT NULL"
            if row['dflt_value']:
                col_def += f" DEFAULT {row['dflt_value']}"
            if row['pk']:
                col_def += " PRIMARY KEY"
            columns.append(col_def)
        
        create_sql = f"""-- Mock table for {real_table_name}
        CREATE TABLE {mock_table_name} (
            {','.join(chr(10) + '    ' + col for col in columns)}
        );

        -- Sample INSERT statements (replace with your mock data)
        -- INSERT INTO {mock_table_name} VALUES (...);
        -- INSERT INTO {mock_table_name} VALUES (...);
        -- INSERT INTO {mock_table_name} VALUES (...);
        """
        
        return create_sql