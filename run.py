# ============================================================================
# run.py (Updated with OpenAI key check)
# ============================================================================
"""
Main entry point for the Flask Text-to-SQL application with OpenAI integration
"""

from app import app
from setup_database import create_sample_database
from config import Config
import os

def check_environment():
    """Check if all required environment variables are set"""
    if not Config.OPENAI_API_KEY:
        print("🚨 ERROR: OpenAI API key not found!")
        print("\n📝 Please follow these steps:")
        print("1. Create a .env file in your project directory")
        print("2. Add your OpenAI API key: OPENAI_API_KEY=your_key_here")
        print("3. Get your API key from: https://platform.openai.com/api-keys")
        print("\n💡 Example .env file:")
        print("OPENAI_API_KEY=sk-your-actual-api-key-here")
        print("FLASK_DEBUG=True")
        return False
    return True

if __name__ == '__main__':
    print("🚀 Starting Flask Text-to-SQL application with OpenAI...")
    
    # Check environment variables
    if not check_environment():
        exit(1)
    
    # Create sample database if it doesn't exist
    if not os.path.exists(Config.DATABASE_PATH):
        print("📊 Creating sample database...")
        create_sample_database(Config.DATABASE_PATH)
        print("✅ Sample database created successfully!")
    
    print(f"\n🔧 Configuration:")
    print(f"   OpenAI Model: {Config.OPENAI_MODEL}")
    print(f"   Database: {Config.DATABASE_PATH}")
    print(f"   Debug Mode: {Config.DEBUG}")
    
    print(f"\n🌐 Access the application at: http://localhost:5000")
    print("\n💬 Sample questions you can try:")
    print("   • Show me all users who joined this year")
    print("   • What are the top 5 most expensive products?")
    print("   • How many orders were placed last month?")
    print("   • Find customers who have never placed an order")
    print("   • Show total revenue by category")
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)