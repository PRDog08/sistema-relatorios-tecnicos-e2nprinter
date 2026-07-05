import os

# =========================
# CONFIGURAÇÕES GERAIS
# =========================

# URL do banco PostgreSQL (Render)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "A variável de ambiente DATABASE_URL não foi configurada."
    )

# Token de acesso ao painel administrativo
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin")

# Nome do sistema
SYSTEM_NAME = "E2nPrinter - Relatórios Técnicos"

# Modo de depuração
DEBUG = os.getenv("DEBUG", "False").strip().lower() == "true"