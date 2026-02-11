# -*- coding: utf-8 -*-
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "database": "estoque_inteligente",
    "user": "postgres",
    "password": "admin",
    "port": "5432"
}

def salvar_preco(dados):
    """
    Recebe um dicionário e salva na tabela bronze.
    Espera: {'nome': str, 'preco': str, 'concorrente': str, 'url': str, 'termo': str}
    """
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO bronze.precos_concorrentes 
                    (produto_nome, preco_raw, concorrente, url_fonte, termo_busca)
                    VALUES (%(nome)s, %(preco)s, %(concorrente)s, %(url)s, %(termo)s);
                """, {
                    'nome': dados['nome'],
                    'preco': dados['preco'],
                    'concorrente': dados['concorrente'],
                    'url': dados['url'],
                    'termo': dados.get('termo', 'Desconhecido') 
                })
                conn.commit()
                print(f"[DB] Salvo com sucesso: {dados['nome'][:50]}...")
    except Exception as e:
        print(f"[DB ERRO] Falha ao conectar ou salvar: {e}")

# Este bloco 'if' serve apenas para testar a conexão isoladamente
if __name__ == "__main__":
    print("Testando conexão com o banco...")
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            print("Conexão OK!")
    except Exception as e:
        print(f"Erro de conexão: {e}")