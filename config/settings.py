from dotenv import load_dotenv
import os

load_dotenv()

# IA
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Google Ads
GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
GOOGLE_ADS_CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
GOOGLE_ADS_CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
GOOGLE_ADS_REFRESH_TOKEN = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
GOOGLE_ADS_LOGIN_CUSTOMER_ID = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")

# Banco
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/unbound_sales.db")

# Geral
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Modelo padrão Claude
DEFAULT_MODEL = "claude-sonnet-4-6"

# Managed Agents — IDs criados via agents/setup_agents.py (adicione ao .env)
MANAGED_AGENTS_ENVIRONMENT_ID = os.getenv("MANAGED_AGENTS_ENVIRONMENT_ID")
AGENT_LUCAS_ID     = os.getenv("AGENT_LUCAS_ID")
AGENT_PEDRO_ID     = os.getenv("AGENT_PEDRO_ID")
AGENT_RODRIGO_ID   = os.getenv("AGENT_RODRIGO_ID")
AGENT_ANA_ID       = os.getenv("AGENT_ANA_ID")
AGENT_MODERADOR_ID = os.getenv("AGENT_MODERADOR_ID")

# Instagram Graph API
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID   = os.getenv("INSTAGRAM_ACCOUNT_ID")

# TikTok API
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")

# Hospedagem de imagens (para publicação no Instagram)
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
