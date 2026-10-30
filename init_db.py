from app import app, inicializar_banco


def criar_tabelas():
    with app.app_context():
        inicializar_banco()
    print("Banco de dados verificado com sucesso.")


if __name__ == "__main__":
    criar_tabelas()
