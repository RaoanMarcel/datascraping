import pandas as pd
import psycopg2
import streamlit as st
from db import DB_CONFIG

def carregar_dados_gold():
    conn = psycopg2.connect(**DB_CONFIG)
    query = "SELECT * FROM gold.historico_precos ORDER BY data_coleta ASC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def carregar_dados_silver(termo=None):
    conn = psycopg2.connect(**DB_CONFIG)
    if termo:
        query = f"""
        SELECT produto_nome, preco_final, concorrente, url_fonte, data_processamento 
        FROM silver.precos_limpos 
        WHERE termo_busca = '{termo}' 
        ORDER BY preco_final ASC
        """
    else:
        query = """
        SELECT produto_nome, preco_final, concorrente, termo_busca, data_processamento 
        FROM silver.precos_limpos 
        ORDER BY data_processamento DESC LIMIT 100
        """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def atualizar_custo_gold(termo, custo):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        query = """
        UPDATE gold.historico_precos
        SET preco_custo = %s
        WHERE termo_busca = %s AND data_coleta = CURRENT_DATE
        """
        cur.execute(query, (custo, termo))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao salvar custo: {e}")