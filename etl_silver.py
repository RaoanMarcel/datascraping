# etl_silver.py
import psycopg2
import re
from db import DB_CONFIG

def limpar_preco_texto(texto):
    """
    Transforma 'R$ 3.749,99' ou 'de R$ 4000 por R$ 3000' em float 3749.99
    """
    try:
        # Regex para pegar o padrão monetário brasileiro (ex: 3.749,99)
        # Pega o último preço encontrado na string (geralmente é o preço 'por', o mais barato)
        valores = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
        
        if not valores:
            return None
            
        # Pega o último valor encontrado (lógica: de X por Y -> queremos Y)
        valor_bruto = valores[-1]
        
        # Converte para formato americano (remove ponto milhar, troca vírgula por ponto)
        valor_limpo = valor_bruto.replace('.', '').replace(',', '.')
        return float(valor_limpo)
    except:
        return None

def executar_etl():
    print("⚙️ [ETL] Iniciando processamento Bronze -> Silver...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 1. Busca dados da Bronze que ainda não foram processados (simplificado: pegamos tudo hoje)
    cur.execute("SELECT id, produto_nome, preco_raw, concorrente FROM bronze.precos_concorrentes")
    dados_bronze = cur.fetchall()
    
    novos_registros = 0
    
    for row in dados_bronze:
        id_bronze, nome, preco_texto, loja = row
        
        preco_decimal = limpar_preco_texto(preco_texto)
        
        if preco_decimal:
            # Verifica se já existe na Silver para não duplicar (idempotência)
            cur.execute("SELECT id FROM silver.precos_limpos WHERE id_bronze = %s", (id_bronze,))
            if cur.fetchone():
                continue
                
            # Insere na Silver
            cur.execute("""
                INSERT INTO silver.precos_limpos (id_bronze, produto_nome, preco_final, concorrente)
                VALUES (%s, %s, %s, %s)
            """, (id_bronze, nome, preco_decimal, loja))
            novos_registros += 1
            
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✨ [ETL] Sucesso! {novos_registros} novos preços limpos e salvos na camada Silver.")

if __name__ == "__main__":
    executar_etl()