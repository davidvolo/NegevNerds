import os

import pytest
from dotenv import load_dotenv

from app import app, db

@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Automatically load environment variables for testing."""
    load_dotenv(dotenv_path=".env.test")  # Specify the path to your .env.test file
    # Optionally, you can print them to verify
    print(f"Test Environment: {os.getenv('APP_ENV', 'production')}")
    print(f"Test DB Path: {os.getenv('DB_PATH', 'default.db')}")

@pytest.fixture(scope="function")
def test_client():
    """Create a clean database for each test."""
    app.config["TESTING"] = True

    # Use the test database from the environment variable
    db_path = os.getenv("DB_PATH", "sqlite:///test_NegevNerds.db")  # Fallback to default test DB
    app.config["SQLALCHEMY_DATABASE_URI"] = db_path  # Set test DB URI

    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Create tables for test
        yield client  # Run the test
        with app.app_context():
            db.drop_all()  # Clean up after test