"""Central config. Read secrets from environment, never hard-code."""
import os

try:
    from dotenv import load_dotenv
except ImportError:  # optional in tests
    def load_dotenv(*_a, **_k):
        return False

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://labellens:labellens@localhost:5432/labellens")
OPENFDA_API_KEY = os.getenv("OPENFDA_API_KEY", "")
SEED = 42
