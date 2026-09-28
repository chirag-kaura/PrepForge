from groq import Groq

from backend.app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)