import os

from dotenv import load_dotenv

load_dotenv()

# DB
DATABASE_URL = os.getenv("DATABASE_URL")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# DEEPSEEK
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

SECRET_KEY = "spoon-ai-secret-key"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
