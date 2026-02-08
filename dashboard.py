import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from db import DB_CONFIG

# --- IMPORTAÇÃO DOS MÓDULOS ---
import kabum
import pichau
import etl_silver
import etl_gold
from utils import analisar_competitividade 

st.set_page_config(page_title="Monitor Pro", layout="wide", page_icon="🦅")

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_dados_gold():
    conn = psycopg2.connect(**DB_CONFIG)
    query = """
    SELECT * FROM gold.historico_precos 
    ORDER BY data_coleta DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def carregar_dados_silver(termo=None):
    conn = psycopg2.connect(**DB_CONFIG)
    if termo:
        # Agora a coluna url_fonte existe no banco
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

# 1. Formulário Otimizado
with st.sidebar.form(key='search_form'):
    st.markdown("### 🕵️ Nova Busca")
    
    # Input do produto
    novo_termo = st.text_input("Produto", placeholder="Ex: iPhone 15", help="Nome do produto para buscar na Web")
    
    # Input do Custo (Agora sozinho e limpo)
    preco_custo_input = st.number_input("Preço de Custo (R$)", min_value=0.0, format="%.2f", help="Seu custo de aquisição para cálculo de margem")
    
    submit_button = st.form_submit_button(label='🚀 Rastrear Agora')

# 2. Área de Admin
with st.sidebar.expander("⚙️ Admin Tools", expanded=False):
    if st.button("🧹 Reprocessar Silver"):
        etl_silver.executar_etl_silver()
        st.toast("Silver atualizado!", icon="✅")
        
    if st.button("🏆 Reprocessar Gold"):
        etl_gold.executar_etl_gold()
        st.toast("Gold atualizado!", icon="✅")

# --- EXECUÇÃO DO PIPELINE ---
if submit_button and novo_termo:
    st.toast(f"Iniciando: {novo_termo}", icon="🤖")
    my_bar = st.progress(0, text="Chamando robôs...")

    try:
        # 1. Robôs
        # kabum.buscar_produtos(novo_termo) # Descomente se quiser rodar scraping
        # my_bar.progress(30, text="Pichau finalizado...")
        # pichau.buscar_produtos(novo_termo) # Descomente se quiser rodar scraping
        
        # MODO TESTE RÁPIDO: Se você já rodou o scraping e só quer testar o código novo,
        # comente as linhas do kabum/pichau acima e rode só os ETLs abaixo.
        
        # 2. ETLs
        my_bar.progress(60, text="Limpando dados...")
        etl_silver.executar_etl_silver()
        my_bar.progress(80, text="Calculando estatísticas...")
        etl_gold.executar_etl_gold()

        # 3. Salvar Custo
        if preco_custo_input > 0:
            atualizar_custo_gold(novo_termo, preco_custo_input)

        my_bar.progress(100, text="Pronto!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Erro: {e}")

# --- DASHBOARD VISUAL ---
df_gold = carregar_dados_gold()

st.title("📊 Monitor de Competitividade")

if not df_gold.empty:
    lista_termos = df_gold['termo_busca'].unique()
    termo_selecionado = st.selectbox("Selecione o Produto:", lista_termos)

    if termo_selecionado:
        # Filtros
        dados_gold_termo = df_gold[df_gold['termo_busca'] == termo_selecionado]
        registro_atual = dados_gold_termo.iloc[0] # Pega o dia mais recente
        
        custo_bd = registro_atual.get('preco_custo')
        menor_preco_mercado = float(registro_atual['preco_minimo'])

        # --- KPI CARDS ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Menor Preço (Web)", f"R$ {menor_preco_mercado:,.2f}")
        col2.metric("Média de Mercado", f"R$ {registro_atual['preco_medio']:,.2f}")
        col3.metric("Loja Vencedora", registro_atual['loja_mais_barata'])
        
        # Mostra o custo se existir
        if custo_bd and custo_bd > 0:
            col4.metric("Meu Custo", f"R$ {custo_bd:,.2f}")
        else:
            col4.metric("Meu Custo", "---")

        # --- ANÁLISE DE INTELIGÊNCIA ---
        if custo_bd and custo_bd > 0:
            analise = analisar_competitividade(float(custo_bd), menor_preco_mercado)
            
            if analise:
                st.markdown("---")
                if analise['status'] == "CRÍTICO":
                    st.error(f"{analise['icone']} **ANÁLISE DE MERCADO:** {analise['msg']}")
                elif analise['status'] == "ALERTA":
                    st.warning(f"{analise['icone']} **ANÁLISE DE MERCADO:** {analise['msg']}")
                else:
                    st.success(f"{analise['icone']} **ANÁLISE DE MERCADO:** {analise['msg']}")

        st.markdown("---")

        # --- GRÁFICOS E TABELAS ---
        tab1, tab2 = st.tabs(["📈 Gráficos", "📋 Lista de Produtos"])

        with tab1:
            fig = px.line(dados_gold_termo, x='data_coleta', y=['preco_minimo', 'preco_medio'], markers=True)
            if custo_bd:
                fig.add_hline(y=custo_bd, line_dash="dot", annotation_text="Seu Custo", annotation_position="bottom right", line_color="red")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            dados_silver = carregar_dados_silver(termo_selecionado)
            
            # Filtro textual simples na tabela
            filtro = st.text_input("Filtrar itens:", placeholder="Ex: Asus")
            if filtro:
                dados_silver = dados_silver[dados_silver['produto_nome'].str.contains(filtro, case=False)]

            st.dataframe(
                dados_silver, 
                use_container_width=True,
                column_config={
                    "preco_final": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
                    "url_fonte": st.column_config.LinkColumn("Link Original", display_text="Acessar Site")
                }
            )
else:
    st.info("Nenhum dado encontrado. Faça sua primeira busca na barra lateral.")