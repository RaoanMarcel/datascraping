import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import warnings
import asyncio
import sys

# --- FIX DO WINDOWS + PLAYWRIGHT ---
# Isso resolve o erro "NotImplementedError" forçando a política correta de eventos
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from db import DB_CONFIG

# --- IMPORTAÇÃO DOS MÓDULOS ---
import kabum
import pichau
import etl_silver
import etl_gold
from utils import analisar_competitividade 

# 1. Configuração da Página e Remoção de Avisos
st.set_page_config(page_title="Monitor Pro", layout="wide", page_icon="🦅")
warnings.filterwarnings('ignore') 

# --- FUNÇÕES DE BANCO DE DADOS ---
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

# --- BARRA LATERAL (CONTROLE) ---
st.sidebar.title("🦅 Comando")
st.sidebar.markdown("---")

with st.sidebar.form(key='search_form'):
    st.markdown("### 🕵️ Nova Busca")
    novo_termo = st.text_input("Produto", placeholder="Ex: iPhone 15", help="Nome do produto para buscar na Web")
    preco_custo_input = st.number_input("Preço de Custo (R$)", min_value=0.0, format="%.2f", help="Seu custo de aquisição")
    submit_button = st.form_submit_button(label='🚀 Rastrear Agora')

with st.sidebar.expander("⚙️ Admin Tools", expanded=False):
    if st.button("🧹 Reprocessar Silver"):
        print("--- ADMIN: INICIANDO ETL SILVER ---")
        etl_silver.executar_etl_silver()
        st.toast("Silver atualizado!", icon="✅")
    if st.button("🏆 Reprocessar Gold"):
        print("--- ADMIN: INICIANDO ETL GOLD ---")
        etl_gold.executar_etl_gold()
        st.toast("Gold atualizado!", icon="✅")

# --- LÓGICA DE EXECUÇÃO E MEMÓRIA ---
if 'ultimo_termo_buscado' not in st.session_state:
    st.session_state['ultimo_termo_buscado'] = None

if submit_button and novo_termo:
    st.session_state['ultimo_termo_buscado'] = novo_termo
    
    # MENSAGEM NO TERMINAL PARA VOCÊ VER QUE COMEÇOU
    print(f"\n🚀 --- INICIANDO RASTREIO PARA: {novo_termo} ---")
    
    with st.status("🤖 Iniciando operação de rastreio...", expanded=True) as status:
        
        # 1. KABUM
        st.write("🔍 Consultando Kabum...")
        print("🔍 [TERMINAL] Chamando robô da Kabum...") 
        try:
            kabum.buscar_produtos(novo_termo)
            st.write("✅ Kabum: OK")
            print("✅ [TERMINAL] Kabum finalizado com sucesso.")
        except Exception as e:
            msg_erro = f"❌ Kabum falhou: {e}"
            st.error(msg_erro)
            print(f"❌ [TERMINAL] {msg_erro}") 

        # 2. PICHAU
        st.write("🔍 Consultando Pichau...")
        print("🔍 [TERMINAL] Chamando robô da Pichau...")
        try:
            pichau.buscar_produtos(novo_termo)
            st.write("✅ Pichau: OK")
            print("✅ [TERMINAL] Pichau finalizado com sucesso.")
        except Exception as e:
            msg_erro = f"❌ Pichau falhou: {e}"
            st.error(msg_erro)
            print(f"❌ [TERMINAL] {msg_erro}")

        # 3. ETLs
        st.write("⚙️ Processando Silver...")
        print("⚙️ [TERMINAL] Rodando ETL Silver...")
        etl_silver.executar_etl_silver()
        
        st.write("🏆 Calculando Gold...")
        print("🏆 [TERMINAL] Rodando ETL Gold...")
        etl_gold.executar_etl_gold()

        # 4. Custo
        if preco_custo_input > 0:
            st.write("💰 Atualizando custos...")
            atualizar_custo_gold(novo_termo, preco_custo_input)

        status.update(label="Rastreio Finalizado!", state="complete", expanded=False)
        print("🏁 [TERMINAL] Rastreio concluído.\n")
    
    st.rerun()

# --- DASHBOARD VISUAL ---
df_gold = carregar_dados_gold()

st.title("📊 Monitor de Competitividade")

if not df_gold.empty:
    lista_termos = sorted(df_gold['termo_busca'].unique())
    
    index_padrao = 0
    if st.session_state['ultimo_termo_buscado'] in lista_termos:
        index_padrao = lista_termos.index(st.session_state['ultimo_termo_buscado'])
    
    termo_selecionado = st.selectbox("Selecione o Produto:", lista_termos, index=index_padrao)

    if termo_selecionado:
        dados_gold_termo = df_gold[df_gold['termo_busca'] == termo_selecionado].sort_values('data_coleta')
        dados_silver_termo = carregar_dados_silver(termo_selecionado)
        
        registro_atual = dados_gold_termo.iloc[-1]
        custo_bd = registro_atual.get('preco_custo')
        menor_preco_mercado = float(registro_atual['preco_minimo'])

        # KPI CARDS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Menor Preço", f"R$ {menor_preco_mercado:,.2f}")
        c2.metric("Média Mercado", f"R$ {registro_atual['preco_medio']:,.2f}")
        c3.metric("Loja Vencedora", registro_atual['loja_mais_barata'])
        c4.metric("Meu Custo", f"R$ {custo_bd:,.2f}" if custo_bd else "---")

        if custo_bd and custo_bd > 0:
            analise = analisar_competitividade(float(custo_bd), menor_preco_mercado)
            if analise:
                st.markdown("---")
                if analise['status'] == "CRÍTICO": st.error(f"{analise['icone']} {analise['msg']}")
                elif analise['status'] == "ALERTA": st.warning(f"{analise['icone']} {analise['msg']}")
                else: st.success(f"{analise['icone']} {analise['msg']}")

        st.markdown("---")

        # GRÁFICOS
        tab1, tab2 = st.tabs(["🦅 Visão Estratégica", "📋 Dados Detalhados"])

        with tab1:
            c_g1, c_g2 = st.columns([2, 1])
            with c_g1:
                st.subheader("📉 Histórico de Preços")
                fig_tunnel = px.area(dados_gold_termo, x='data_coleta', y='preco_minimo', markers=True)
                if custo_bd: fig_tunnel.add_hline(y=custo_bd, line_dash="dot", line_color="red", annotation_text="Custo")
                st.plotly_chart(fig_tunnel, width="stretch")
            
            with c_g2:
                st.subheader("🏆 Share of Buy Box")
                df_share = dados_gold_termo['loja_mais_barata'].value_counts().reset_index()
                st.plotly_chart(px.pie(df_share, values='count', names='loja_mais_barata', hole=0.4), width="stretch")

            st.divider()
            c_g3, c_g4 = st.columns(2)
            
            with c_g3:
                st.subheader("📦 Dispersão (Hoje)")
                if not dados_silver_termo.empty:
                    fig_box = px.box(dados_silver_termo, x="preco_final", points="all", hover_data=["concorrente"])
                    if custo_bd: fig_box.add_vline(x=custo_bd, line_color="red")
                    st.plotly_chart(fig_box, width="stretch")
            
            with c_g4:
                st.subheader("⚔️ Ranking Médio")
                if not dados_silver_termo.empty:
                    df_agg = dados_silver_termo.groupby('concorrente')['preco_final'].mean().reset_index().sort_values('preco_final')
                    st.plotly_chart(px.bar(df_agg, x='preco_final', y='concorrente', orientation='h', text_auto='.2s'), width="stretch")

        with tab2:
            st.dataframe(dados_silver_termo, width="stretch")
else:
    st.info("👈 Utilize o menu lateral para fazer sua primeira busca.")