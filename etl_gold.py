import psycopg2
from db import DB_CONFIG

def executar_etl_gold():
    print("🏆 [ETL GOLD] Calculando estatísticas diárias...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # A Mágica do array_agg:
    # (array_agg(concorrente ORDER BY preco_final ASC))[1]
    # Isso cria uma lista de lojas ordenadas do mais barato pro mais caro e pega a primeira [1].
    # Resolve o problema do GROUP BY sem precisar de subquery complexa.
    
    query_analitica = """
    INSERT INTO gold.historico_precos 
    (termo_busca, data_coleta, loja_mais_barata, preco_minimo, preco_medio, preco_maximo, qtd_itens_encontrados)
    SELECT 
        termo_busca,
        DATE(data_processamento) as data_coleta,
        (array_agg(concorrente ORDER BY preco_final ASC))[1] as loja_mais_barata,
        MIN(preco_final) as preco_minimo,
        ROUND(AVG(preco_final), 2) as preco_medio,
        MAX(preco_final) as preco_maximo,
        COUNT(*) as qtd
    FROM silver.precos_limpos
    WHERE termo_busca IS NOT NULL 
      AND termo_busca != 'Desconhecido'
      -- Filtro Anti-Ruído (Remove Energéticos e itens errados)
      AND produto_nome ILIKE '%%' || termo_busca || '%%'
    GROUP BY termo_busca, DATE(data_processamento)
    ON CONFLICT (termo_busca, data_coleta) 
    DO UPDATE SET 
        loja_mais_barata = EXCLUDED.loja_mais_barata,
        preco_minimo = EXCLUDED.preco_minimo,
        preco_medio = EXCLUDED.preco_medio,
        preco_maximo = EXCLUDED.preco_maximo,
        qtd_itens_encontrados = EXCLUDED.qtd_itens_encontrados;
    """
    
    try:
        # Garante que o índice existe para o ON CONFLICT funcionar
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_gold_termo_data 
            ON gold.historico_precos (termo_busca, data_coleta);
        """)
        
        cur.execute(query_analitica)
        registros = cur.rowcount
        conn.commit()
        print(f"✨ [GOLD] Sucesso! {registros} históricos diários gerados.")
        
    except Exception as e:
        print(f"❌ Erro no ETL Gold: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    executar_etl_gold()