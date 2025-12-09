import os
import sys
import pytest
from dotenv import load_dotenv

# Add the project root directory to sys.path so we can import modules from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()

@pytest.fixture
def substack_credentials():
    email = os.getenv("SUBSTACK_EMAIL")
    password = os.getenv("SUBSTACK_PASSWORD")
    url = os.getenv("SUBSTACK_URL")
    
    if not (email and password and url):
        pytest.skip("Skipping integration test: Missing credentials in .env")
        
    return {
        "email": email,
        "password": password,
        "url": url
    }
