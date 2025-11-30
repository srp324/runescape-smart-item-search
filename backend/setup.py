"""
Setup configuration for the backend package.
This allows the backend to be installed in development mode for easier testing.
"""

from setuptools import setup, find_packages

setup(
    name="runescape-item-search-backend",
    version="1.0.0",
    description="Backend for RuneScape Smart Item Search",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.9",
        "pgvector>=0.2.3",
        "sentence-transformers>=2.7.0",
        "transformers>=4.51.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.11.1",
            "httpx>=0.24.0",
        ],
        "dev": [
            "flake8>=6.1.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
        ]
    }
)

