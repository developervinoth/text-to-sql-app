"""
Final Flask Text-to-SQL Application with PCI/MNPI Compliance
Complete secure implementation with OpenAI integration
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from config import Config
from models.database import DatabaseManager
from services.secure_text_to_sql_service import SecureTextToSQLService
import os
import logging
from datetime import datetime
import traceback

# Configure comprehensive logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper() if hasattr(Config, 'LOG_LEVEL') else 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Global variables for services
db_manager = None
text_to_sql_service = None
app_start_time = datetime.now()

def initialize_services():
    """Initialize database manager and secure text-to-SQL service"""
    global db_manager, text_to_sql_service
    
    try:
        logger.info("Initializing application services...")
        
        # Check if database exists
        if not os.path.exists(app.config['DATABASE_PATH']):
            logger.error(f"Database file not found: {app.config['DATABASE_PATH']}")
            logger.info("Please run 'python setup_database.py' to create the database")
            return False
        
        # Initialize database manager
        db_manager = DatabaseManager(app.config['DATABASE_PATH'])
        logger.info(f"Database manager initialized: {app.config['DATABASE_PATH']}")
        
        # Initialize secure text-to-SQL service
        text_to_sql_service = SecureTextToSQLService(db_manager)
        logger.info("Secure text-to-SQL service initialized")
        
        # Log security status
        compliance = text_to_sql_service.validate_security_compliance()
        logger.info(f"Security compliance: {compliance['compliance_percentage']:.1f}% ({compliance['security_level']})")
        
        if not compliance['is_fully_compliant']:
            logger.warning(f"Missing mock tables for: {compliance['missing_mock_tables']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        logger.error(traceback.format_exc())
        return False

# Initialize services on startup
services_initialized = initialize_services()

# ============================================================================
# ROUTE HANDLERS
# ============================================================================

@app.route('/')
def index():
    """Render the main page"""
    try:
        if not services_initialized:
            return render_template_string("""
            <html><body>
                <h1>⚠️ Application Not Ready</h1>
                <p>The application could not initialize properly.</p>
                <p>Please check the logs and ensure the database is set up correctly.</p>
                <p>Run: <code>python setup_database.py</code></p>
            </body></html>
            """), 500
        
        return render_template('index.html')
        
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return f"Error loading application: {str(e)}", 500

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process natural language query and return SQL results"""
    if not services_initialized or not text_to_sql_service:
        return jsonify({
            'success': False,
            'error': 'Application services not properly initialized',
            'suggestion': 'Please restart the application or check the logs'
        }), 500
    
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'No question provided',
                'suggestion': 'Please provide a question in the request body'
            }), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({
                'success': False,
                'error': 'Empty question provided',
                'suggestion': 'Please enter a valid question'
            }), 400
        
        # Log the request
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        logger.info(f"Processing query from {client_ip}: {question[:100]}...")
        
        # Process the question securely
        result = text_to_sql_service.process_question(question)
        
        # Log the result
        if result['success']:
            logger.info(f"Query successful: {result['query'][:100]}..., returned {result['result']['row_count']} rows")
        else:
            logger.warning(f"Query failed: {result['error']}")
        
        # Add metadata to response
        result['metadata'] = {
            'processing_time': 'calculated_on_frontend',
            'security_mode': 'PCI/MNPI_compliant',
            'api_version': '1.0.0'
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'suggestion': 'Please try again or contact support if the issue persists'
        }), 500

@app.route('/api/database-info')
def get_database_info():
    """Get database schema information with security status"""
    if not services_initialized or not text_to_sql_service:
        return jsonify({
            'success': False,
            'error': 'Application services not properly initialized'
        }), 500
    
    try:
        info = text_to_sql_service.get_database_info()
        logger.debug("Database info retrieved successfully")
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
    if not services_initialized or not text_to_sql_service:
        return jsonify({
            'success': False,
            'error': 'Application services not properly initialized'
        }), 500
    
    try:
        logger.info("Refreshing database schema cache...")
        text_to_sql_service.refresh_context()
        
        # Get updated info
        info = text_to_sql_service.get_database_info()
        
        logger.info("Schema refreshed successfully")
        return jsonify({
            'success': True,
            'message': 'Schema refreshed successfully',
            'updated_info': info
        })
        
    except Exception as e:
        logger.error(f"Error refreshing schema: {e}")
        return jsonify({
            'success': False,
            'error': f'Error refreshing schema: {str(e)}'
        }), 500

@app.route('/api/openai-status')
def check_openai_status():
    """Check OpenAI API status and configuration"""
    if not services_initialized or not text_to_sql_service:
        return jsonify({
            'success': False,
            'error': 'Application services not properly initialized'
        }), 500
    
    try:
        is_connected = text_to_sql_service.test_openai_connection()
        
        return jsonify({
            'success': True,
            'openai_connected': is_connected,
            'model': Config.OPENAI_MODEL,
            'api_configured': bool(Config.OPENAI_API_KEY),
            'temperature': getattr(Config, 'OPENAI_TEMPERATURE', 0.1),
            'max_tokens': getattr(Config, 'OPENAI_MAX_TOKENS', 500)
        })
        
    except Exception as e:
        logger.error(f"Error checking OpenAI status: {e}")
        return jsonify({
            'success': False,
            'error': f'Error checking OpenAI status: {str(e)}',
            'openai_connected': False
        }), 500

@app.route('/api/security-status')
def get_security_status():
    """Get detailed security compliance status"""
    if not services_initialized or not text_to_sql_service:
        return jsonify({
            'success': False,
            'error': 'Application services not properly initialized'
        }), 500
    
    try:
        compliance = text_to_sql_service.validate_security_compliance()
        table_status = text_to_sql_service.get_table_sample_status()
        
        return jsonify({
            'success': True,
            'compliance': compliance,
            'table_status': table_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        return jsonify({
            'success': False,
            'error': f'Error getting security status: {str(e)}'
        }), 500

@app.route('/api/health')
def get_health():
    """Get comprehensive application health status"""
    try:
        if not services_initialized or not text_to_sql_service:
            return jsonify({
                'status': 'unhealthy',
                'error': 'Services not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        health = text_to_sql_service.get_service_health()
        
        # Add application-level health info
        health.update({
            'app_uptime_seconds': (datetime.now() - app_start_time).total_seconds(),
            'database_path': app.config['DATABASE_PATH'],
            'debug_mode': app.config['DEBUG'],
            'flask_env': app.config.get('ENV', 'unknown')
        })
        
        return jsonify(health)
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/mock-setup-script')
def get_mock_setup_script():
    """Get SQL script to create missing mock tables"""
    if not services_initialized or not text_to_sql_service:
        return jsonify({
            'success': False,
            'error': 'Application services not properly initialized'
        }), 500
    
    try:
        script = text_to_sql_service.generate_mock_setup_script()
        
        return jsonify({
            'success': True,
            'script': script,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating mock setup script: {e}")
        return jsonify({
            'success': False,
            'error': f'Error generating script: {str(e)}'
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/api/query',
            '/api/database-info',
            '/api/openai-status',
            '/api/security-status',
            '/api/health'
        ]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'suggestion': 'Check the HTTP method (GET/POST) for this endpoint'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'suggestion': 'Please try again or contact support'
    }), 500

# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================


@app.teardown_appcontext
def close_db(error):
    """Close database connection on request completion"""
    if db_manager and hasattr(db_manager, 'close'):
        try:
            db_manager.close()
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

@app.teardown_request
def log_request(error):
    """Log request completion"""
    if error:
        logger.error(f"Request completed with error: {error}")

# ============================================================================
# DEVELOPMENT HELPERS
# ============================================================================

@app.route('/api/config')
def get_config():
    """Get safe configuration info (development only)"""
    if not app.config['DEBUG']:
        return jsonify({'error': 'Not available in production'}), 403
    
    safe_config = {
        'DATABASE_PATH': app.config['DATABASE_PATH'],
        'MAX_QUERY_RESULTS': app.config['MAX_QUERY_RESULTS'],
        'DEBUG': app.config['DEBUG'],
        'OPENAI_MODEL': Config.OPENAI_MODEL,
        'API_KEY_CONFIGURED': bool(Config.OPENAI_API_KEY),
        'SERVICES_INITIALIZED': services_initialized
    }
    
    return jsonify(safe_config)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def render_template_string(template_string, **context):
    """Simple template string renderer for error pages"""
    for key, value in context.items():
        template_string = template_string.replace(f'{{{{{key}}}}}', str(value))
    return template_string

def validate_environment():
    """Validate environment configuration"""
    issues = []
    
    if not Config.OPENAI_API_KEY:
        issues.append("OPENAI_API_KEY not configured")
    
    if not os.path.exists(app.config['DATABASE_PATH']):
        issues.append(f"Database file not found: {app.config['DATABASE_PATH']}")
    
    return issues

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Validate environment before starting
    env_issues = validate_environment()
    if env_issues:
        logger.error("Environment validation failed:")
        for issue in env_issues:
            logger.error(f"  - {issue}")
        
        if not Config.OPENAI_API_KEY:
            logger.error("\n🚨 SETUP REQUIRED:")
            logger.error("1. Create a .env file in your project directory")
            logger.error("2. Add: OPENAI_API_KEY=your-actual-api-key-here")
            logger.error("3. Get your key from: https://platform.openai.com/api-keys")
        
        if not os.path.exists(app.config['DATABASE_PATH']):
            logger.error("\n📊 DATABASE SETUP REQUIRED:")
            logger.error("Run: python setup_database.py")
    
    # Start the application
    logger.info(f"\n🌐 Starting server on http://localhost:5000")
    logger.info("📖 API Documentation available at /api/health")
    
    try:
        app.run(
            debug=app.config['DEBUG'],
            host='0.0.0.0',
            port=5000,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("\n👋 Application stopped by user")
    except Exception as e:
        logger.error(f"\n💥 Application crashed: {e}")
        logger.error(traceback.format_exc())
    finally:
        if db_manager:
            db_manager.close()
        logger.info("🔒 Database connections closed")