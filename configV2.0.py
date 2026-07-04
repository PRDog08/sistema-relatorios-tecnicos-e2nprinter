import os

# =========================
# CONFIGURAÇÕES GERAIS
# =========================

# URL do banco PostgreSQL (Render)
DATABASE_URL = os.getenv("DATABASE_URL")

# Token de admin (painel)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin")

# Nome padrão do sistema
SYSTEM_NAME = "E2nPrinter - Relatórios Técnicos"

# Debug (local)
DEBUG = os.getenv("DEBUG", "False").lower() == "true"