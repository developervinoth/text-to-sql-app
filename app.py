
# ============================================================================
# app.py (Updated with better logging and error handling)
# ============================================================================
from flask import Flask, request, jsonify, render_template
from config import Config
from models.database import DatabaseManager
from services.text_to_sql_service import TextToSQLService
from services.enhanced_text_to_sql_service import EnhancedTextToSQLService
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database manager and service
try:
    db_manager = DatabaseManager(app.config['DATABASE_PATH'])
        # In your app.py, replace the TextToSQLService with:
    enhanced_service = EnhancedTextToSQLService(db_manager)

    # Process questions with table limits:


    text_to_sql_service = TextToSQLService(db_manager)
    logger.info("Application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize application: {e}")
    text_to_sql_service = None

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process natural language query and return SQL results"""
    if not text_to_sql_service:
        return jsonify({
            'success': False,
            'error': 'Application not properly initialized'
        }), 500
    
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'No question provided'
            }), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({
                'success': False,
                'error': 'Empty question provided'
            }), 400
        
        logger.info(f"Received question: {question}")
        
        # Process the question
        # result = text_to_sql_service.process_question(question)
        result = enhanced_service.process_question(question, max_tables=15)
        # Log the result for debugging
        if result['success']:
            logger.info(f"Query successful: {result['query']}, returned {result['result']['row_count']} rows")
        else:
            logger.warning(f"Query failed: {result['error']}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/database-info')
def get_database_info():
    """Get database schema information"""
    if not text_to_sql_service:
        return jsonify({
            'success': False,
            'error': 'Application not properly initialized'
        }), 500
    
    try:
        info = text_to_sql_service.get_database_info()
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting database info: {str(e)}'
        }), 500

@app.route('/api/refresh-schema', methods=['POST'])
def refresh_schema():
    """Refresh database schema cache"""
    if not text_to_sql_service:
        return jsonify({
            'success': False,
            'error': 'Application not properly initialized'
        }), 500
    
    try:
        text_to_sql_service.refresh_context()
        return jsonify({
            'success': True,
            'message': 'Schema refreshed successfully'
        })
    except Exception as e:
        logger.error(f"Error refreshing schema: {e}")
        return jsonify({
            'success': False,
            'error': f'Error refreshing schema: {str(e)}'
        }), 500

@app.route('/api/openai-status')
def check_openai_status():
    """Check OpenAI API status"""
    if not text_to_sql_service:
        return jsonify({
            'success': False,
            'error': 'Application not properly initialized'
        }), 500
    
    try:
        status = text_to_sql_service.test_openai_connection()
        return jsonify({
            'success': True,
            'openai_connected': status,
            'model': Config.OPENAI_MODEL
        })
    except Exception as e:
        logger.error(f"Error checking OpenAI status: {e}")
        return jsonify({
            'success': False,
            'error': f'Error checking OpenAI status: {str(e)}'
        }), 500

@app.teardown_appcontext
def close_db(error):
    """Close database connection"""
    if db_manager and hasattr(db_manager, 'close'):
        db_manager.close()

if __name__ == '__main__':
    if not Config.OPENAI_API_KEY:
        print("WARNING: OpenAI API key not found!")
        print("Please create a .env file with your OPENAI_API_KEY")
    
    app.run(debug=app.config['DEBUG'])

