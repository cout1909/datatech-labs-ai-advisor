"""Print only model IDs and sanitized error codes, never credentials or request headers."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from groq import Groq, APIStatusError
from app.config import settings

try:
    client = Groq(api_key=settings.groq_api_key.get_secret_value(), max_retries=0, timeout=20)
    models = client.models.list()
    print('Configured model:', settings.groq_model)
    print('Available models:', ', '.join(sorted(model.id for model in models.data)))
except APIStatusError as exc:
    print('Provider status:', exc.status_code)
    print('Error code:', getattr(exc, 'code', None))
    raise SystemExit(1)
