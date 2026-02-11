import pandas as pd
import psycopg2
from db import DB_CONFIG
from datetime import datetime

def executar_etl_gold():
    print("🏆 [GOLD] Iniciando processamento inteligente...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    query = """
    SELECT termo_busca, concorrente, preco_final, data_processamento 
    FROM silver.precos_limpos
    """
    df = pd.read_sql(query, conn)
    
    if df.empty:
        print("⚠️ [GOLD] Sem dados na Silver para processar.")
        conn.close()
        return

    dados_gold = []
    
    termos_unicos = df['termo_busca'].unique()
    
    for termo in termos_unicos:
        df_termo = df[df['termo_busca'] == termo].copy()
        
        if df_termo.empty: continue
        
        mediana = df_termo['preco_final'].median()
        
        limite_inferior = mediana * 0.40
        
        limite_superior = mediana * 3.0
        
        df_limpo = df_termo[
            (df_termo['preco_final'] >= limite_inferior) & 
            (df_termo['preco_final'] <= limite_superior)
        ]
        
        if df_limpo.empty:
            df_limpo = df_termo
            
        preco_min = df_limpo['preco_final'].min()
        preco_med = df_limpo['preco_final'].mean()
        preco_max = df_limpo['preco_final'].max()
        qtd_itens = len(df_limpo)
        
        # Descobre quem é a loja vencedora (baseado nos dados limpos)
        row_vencedora = df_limpo.loc[df_limpo['preco_final'].idxmin()]
        loja_vencedora = row_vencedora['concorrente']
        
        dados_gold.append((
            termo,
            datetime.now().date(),
            loja_vencedora,
            float(preco_min),
            float(preco_med),
            float(preco_max),
            int(qtd_itens)
        ))

    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM gold.historico_precos WHERE data_coleta = CURRENT_DATE")
        
        query_insert = """
        INSERT INTO gold.historico_precos 
        (termo_busca, data_coleta, loja_mais_barata, preco_minimo, preco_medio, preco_maximo, qtd_itens_encontrados)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cur.executemany(query_insert, dados_gold)
        conn.commit()
        print(f"✨ [GOLD] Sucesso! {len(dados_gold)} estatísticas calculadas e salvas.")
        
    except Exception as e:
        print(f"❌ [GOLD] Erro ao salvar: {e}")
        conn.rollback()
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    executar_etl_gold()