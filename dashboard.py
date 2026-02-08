import streamlit as st
import warnings
import asyncio
import sys

# --- FIX DO WINDOWS ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# --- IMPORTAÇÕES MÓDULOS PRÓPRIOS ---
import kabum
import pichau
import etl_silver
import etl_gold
import db_functions as db  # Nossas funções de banco
import ui_view as ui       # Nossos gráficos

# 1. Configuração
st.set_page_config(page_title="Monitor Pro", layout="wide", page_icon="🦅")
warnings.filterwarnings('ignore') 

# --- BARRA LATERAL (CONTROLE) ---
st.sidebar.title("🦅 Comando")
st.sidebar.markdown("---")

with st.sidebar.form(key='search_form'):
    st.markdown("### 🕵️ Nova Busca")
    novo_termo = st.text_input("Produto", placeholder="Ex: iPhone 15", help="Nome do produto para buscar na Web")
    preco_custo_input = st.number_input("Preço de Custo (R$)", min_value=0.0, format="%.2f")
    
    st.markdown("### 🏪 Lojas Alvo")
    # Layout em colunas para as checkboxes ficarem bonitas
    col_check1, col_check2 = st.columns(2)
    with col_check1:
        check_kabum = st.checkbox("Kabum", value=True) # value=True começa marcado
    with col_check2:
        check_pichau = st.checkbox("Pichau", value=True)
    
    st.markdown("---")
    submit_button = st.form_submit_button(label='🚀 Rastrear Agora')

with st.sidebar.expander("⚙️ Admin Tools", expanded=False):
    if st.button("🧹 Reprocessar Silver"):
        etl_silver.executar_etl_silver()
        st.toast("Silver atualizado!", icon="✅")
    if st.button("🏆 Reprocessar Gold"):
        etl_gold.executar_etl_gold()
        st.toast("Gold atualizado!", icon="✅")

# --- LÓGICA DE EXECUÇÃO ---
if 'ultimo_termo_buscado' not in st.session_state:
    st.session_state['ultimo_termo_buscado'] = None

if submit_button and novo_termo:
    st.session_state['ultimo_termo_buscado'] = novo_termo
    
    with st.status("🤖 Iniciando operação de rastreio...", expanded=True) as status:
        
        # 1. KABUM (Só roda se o checkbox estiver marcado)
        if check_kabum:
            st.write("🔍 Consultando Kabum...")
            try: 
                kabum.buscar_produtos(novo_termo)
            except Exception as e: 
                st.error(f"Kabum: {e}")
        else:
            st.warning("⚠️ Pulando Kabum (Desativado)")

        # 2. PICHAU (Só roda se o checkbox estiver marcado)
        if check_pichau:
            st.write("🔍 Consultando Pichau...")
            try: 
                pichau.buscar_produtos(novo_termo)
            except Exception as e: 
                st.error(f"Pichau: {e}")
        else:
            st.warning("⚠️ Pulando Pichau (Desativado)")

        # 3. ETLs (Sempre rodam para garantir que os dados novos apareçam)
        st.write("⚙️ Processando ETLs...")
        etl_silver.executar_etl_silver()
        etl_gold.executar_etl_gold()

        if preco_custo_input > 0:
            db.atualizar_custo_gold(novo_termo, preco_custo_input)

        status.update(label="Rastreio Finalizado!", state="complete", expanded=False)
    
    st.rerun()

# --- DASHBOARD VISUAL ---
# (Essa parte continua idêntica, chamando as views e funções separadas)
st.title("📊 Monitor de Competitividade")
df_gold = db.carregar_dados_gold()

if not df_gold.empty:
    lista_termos = sorted(df_gold['termo_busca'].unique())
    index_padrao = 0
    
    if st.session_state['ultimo_termo_buscado'] in lista_termos:
        index_padrao = lista_termos.index(st.session_state['ultimo_termo_buscado'])
    
    termo_selecionado = st.selectbox("Selecione o Produto:", lista_termos, index=index_padrao)

    if termo_selecionado:
        # Carrega dados
        dados_gold_termo = df_gold[df_gold['termo_busca'] == termo_selecionado].sort_values('data_coleta')
        dados_silver_termo = db.carregar_dados_silver(termo_selecionado)
        
        # Prepara variáveis
        registro_atual = dados_gold_termo.iloc[-1]
        custo_bd = registro_atual.get('preco_custo')
        menor_preco = float(registro_atual['preco_minimo'])

        # RENDERIZA A TELA (Chamando o ui_view.py)
        ui.renderizar_kpis(registro_atual, custo_bd, menor_preco)
        ui.renderizar_graficos(dados_gold_termo, dados_silver_termo, custo_bd)
else:
    st.info("👈 Utilize o menu lateral para fazer sua primeira busca.")