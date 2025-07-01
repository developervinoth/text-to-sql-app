
# ============================================================================
# services/openai_service.py (New file for OpenAI integration)
# ============================================================================
import openai
from typing import Optional
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file")
        
        openai.api_key = Config.OPENAI_API_KEY
        self.model = Config.OPENAI_MODEL
        self.temperature = Config.OPENAI_TEMPERATURE
        self.max_tokens = Config.OPENAI_MAX_TOKENS
        
        logger.info(f"OpenAI service initialized with model: {self.model}")
    
    def generate_sql(self, prompt: str) -> Optional[str]:
        """
        Generate SQL query using OpenAI API
        
        Args:
            prompt (str): The text-to-SQL prompt with schema information
            
        Returns:
            str: Generated SQL query or None if error
        """
        try:
            logger.info("Sending request to OpenAI API...")
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert SQL query generator. You convert natural language questions into valid SQLite queries. Always respond with ONLY the SQL query, no explanations or markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            if response.choices and len(response.choices) > 0:
                sql_query = response.choices[0].message.content.strip()
                logger.info(f"Generated SQL: {sql_query}")
                return sql_query
            else:
                logger.error("No response choices received from OpenAI")
                return None
                
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            return None
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {e}")
            return None
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI API: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test the OpenAI API connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": "SELECT 1;"
                    }
                ],
                max_tokens=10,
                temperature=0
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False