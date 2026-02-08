import psycopg2
import re
from db import DB_CONFIG

def limpar_preco_texto(texto):
    """Remove R$, pontos extras e converte para float"""
    try:
        # Regex busca apenas números no formato brasileiro ou americano
        valores = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})|(\d{1,3}(?:,\d{3})*\.\d{2})', texto)
        if not valores: return None
        
        # Pega o último valor encontrado (geralmente o preço principal)
        valor_encontrado = valores[-1][0] if valores[-1][0] else valores[-1][1]
        
        # Padroniza para formato Python (ponto como decimal)
        # Remove pontos de milhar e troca vírgula decimal por ponto
        return float(valor_encontrado.replace('.', '').replace(',', '.'))
    except:
        return None

def executar_etl_silver(): # <--- Nome da função ajustado para o Dashboard
    print("⚙️ [ETL SILVER] Iniciando processamento...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 1. LIMPEZA (TRUNCATE)
    # Importante: Apaga a tabela Silver para recriar do zero.
    # Isso garante que o botão "Reprocessar" do dashboard atualize links e correções.
    cur.execute("TRUNCATE TABLE silver.precos_limpos;")
    
    # 2. LEITURA (Bronze)
    # Adicionamos 'url_fonte' na seleção
    cur.execute("""
        SELECT id, produto_nome, preco_raw, concorrente, termo_busca, url_fonte 
        FROM bronze.precos_concorrentes
    """)
    dados = cur.fetchall()
    
    processados = 0
    for row in dados:
        id_b, nome, preco_txt, loja, termo, url = row # <--- Recupera a URL
        
        preco_dec = limpar_preco_texto(preco_txt)
        
        if preco_dec:
            # 3. CARGA (Silver)
            # Insere os dados limpos incluindo a URL
            cur.execute("""
                INSERT INTO silver.precos_limpos 
                (id_bronze, produto_nome, preco_final, concorrente, termo_busca, url_fonte, data_processamento)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (id_b, nome, preco_dec, loja, termo, url))
            
            processados += 1
            
    conn.commit()
    cur.close()
    conn.close()
    print(f"✨ [SILVER] {processados} registros limpos e atualizados com sucesso.")

if __name__ == "__main__":
    executar_etl_silver()