# etl_silver.py (Atualizado)
import psycopg2
import re
from db import DB_CONFIG

def limpar_preco_texto(texto):
    try:
        valores = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
        if not valores: return None
        return float(valores[-1].replace('.', '').replace(',', '.'))
    except:
        return None

def executar_etl():
    print("⚙️ [ETL SILVER] Processando dados...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Busca inclusive o termo_busca
    cur.execute("SELECT id, produto_nome, preco_raw, concorrente, termo_busca FROM bronze.precos_concorrentes")
    dados = cur.fetchall()
    
    novos = 0
    for row in dados:
        id_b, nome, preco_txt, loja, termo = row # Desempacota o termo
        preco_dec = limpar_preco_texto(preco_txt)
        
        if preco_dec:
            # Verifica duplicidade
            cur.execute("SELECT id FROM silver.precos_limpos WHERE id_bronze = %s", (id_b,))
            if not cur.fetchone():
                # Salva com o termo
                cur.execute("""
                    INSERT INTO silver.precos_limpos 
                    (id_bronze, produto_nome, preco_final, concorrente, termo_busca)
                    VALUES (%s, %s, %s, %s, %s)
                """, (id_b, nome, preco_dec, loja, termo))
                novos += 1
                
    conn.commit()
    cur.close()
    conn.close()
    print(f"✨ [SILVER] {novos} novos registros processados.")

if __name__ == "__main__":
    executar_etl()