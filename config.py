
# ============================================================================
# config.py (Updated with OpenAI settings)
# ============================================================================
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'text_to_sql.db'
    MAX_QUERY_RESULTS = int(os.environ.get('MAX_QUERY_RESULTS', 100))
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4.1')  # or 'gpt-3.5-turbo'
    OPENAI_TEMPERATURE = float(os.environ.get('OPENAI_TEMPERATURE', 0.1))
    OPENAI_MAX_TOKENS = int(os.environ.get('OPENAI_MAX_TOKENS', 500))

