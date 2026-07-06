import os

# =========================
# CONFIGURAÇÕES GERAIS
# =========================

# Banco de dados
# Local: SQLite
# Produção (Render): PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///relatorios.db")

# Corrige URLs antigas do Render
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

# Token de acesso ao painel administrativo
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin")

# Nome do sistema
SYSTEM_NAME = "E2nPrinter - Relatórios Técnicos"

# Modo de depuração
DEBUG = os.getenv("DEBUG", "False").strip().lower() == "true"