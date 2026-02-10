import streamlit as st
import warnings
import asyncio
import sys
import json
import os
import pandas as pd
import time

# Fix para loop de eventos no Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# --- IMPORTAÇÕES DAS LOJAS ---
import kabum
import pichau
import terabyte
import mercadolivre  # <--- IMPORT NOVO AQUI
import etl_silver
import etl_gold
import db_functions as db
import ui_view as ui

# Configuração da Página
st.set_page_config(page_title="Monitor Pro", layout="wide")
warnings.filterwarnings('ignore') 

# CSS: Visual Limpo
st.markdown("""
<style>
    div[data-testid="InputInstructions"] > span:nth-child(1) { display: none; }
    div[data-baseweb="input"] > div { padding: 8px 10px; }
    input[class] { font-size: 1.1rem; }
    label[data-baseweb="label"] { font-size: 0.9rem; font-weight: 600; margin-bottom: 5px; color: #444; }
    section[data-testid="stSidebar"] { padding-top: 20px; }
</style>
""", unsafe_allow_html=True)

CONFIG_FILE = 'config.json'

def carregar_config():
    if not os.path.exists(CONFIG_FILE):
        return {"telegram_token": "", "telegram_chat_id": "", "frequencia_minutos": 60}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def salvar_config(novos_dados):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(novos_dados, f, indent=4)

# ==========================================
# BARRA LATERAL
# ==========================================
st.sidebar.title("Monitor Pro v3.0")
st.sidebar.markdown("---")

# 1. ÁREA DE BUSCA
st.sidebar.subheader("Nova Varredura")
novo_termo = st.sidebar.text_input("Produto", placeholder="Ex: RTX 4060")

st.sidebar.write("Lojas:")
c1, c2 = st.sidebar.columns(2)

check_kabum = c1.checkbox("Kabum", value=True)
check_pichau = c2.checkbox("Pichau", value=True)

c3, c4 = st.sidebar.columns(2)
check_tera = c3.checkbox("Terabyte", value=True)
check_ml = c4.checkbox("ML", value=True)

if st.sidebar.button("Iniciar Busca", type="primary"):
    if novo_termo:
        st.session_state['ultimo_produto_visto'] = novo_termo
        
        status_box = st.sidebar.status("Processando...", expanded=True)
        
        # --- Lógica de Execução ---
        if check_kabum:
            status_box.write("🔎 Consultando Kabum...")
            try: kabum.buscar_produtos(novo_termo)
            except Exception as e: status_box.error(f"Erro Kabum: {e}")
        
        if check_pichau:
            status_box.write("🔎 Consultando Pichau...")
            try: pichau.buscar_produtos(novo_termo)
            except Exception as e: status_box.error(f"Erro Pichau: {e}")

        if check_tera:
            status_box.write("🔎 Consultando Terabyte...")
            try: terabyte.buscar_produtos(novo_termo)
            except Exception as e: status_box.error(f"Erro Tera: {e}")

        if check_ml:  # <--- CHAMADA NOVA
            status_box.write("🔎 Consultando Mercado Livre...")
            try: mercadolivre.buscar_produtos(novo_termo)
            except Exception as e: status_box.error(f"Erro ML: {e}")

        status_box.write("⚙️ Atualizando base (ETL)...")
        etl_silver.executar_etl_silver()
        etl_gold.executar_etl_gold()
        
        status_box.update(label="Concluído!", state="complete", expanded=False)
        time.sleep(1)
        st.rerun()
    else:
        st.sidebar.warning("Digite um nome.")

st.sidebar.markdown("---")

# 2. FILTROS GLOBAIS
st.sidebar.subheader("Filtros de Visualização")
min_val, max_val = st.sidebar.slider(
    "Faixa de Preço (R$)", 
    0.0, 20000.0, (100.0, 20000.0)
)

st.sidebar.markdown("---")

# 3. ÁREA ADMIN
with st.sidebar.expander("Admin & Configurações"):
    config_atual = carregar_config()
    with st.form("admin_form"):
        st.markdown("**Telegram Config**")
        token = st.text_input("Bot Token", value=config_atual.get("telegram_token", ""), type="password")
        chat_id = st.text_input("Chat ID", value=config_atual.get("telegram_chat_id", ""))
        
        st.markdown("---")
        st.markdown("**Automação**")
        freq = st.number_input("Intervalo (min)", value=int(config_atual.get("frequencia_minutos", 60)))
        
        if st.form_submit_button("Salvar Configurações"):
            salvar_config({
                "telegram_token": token,
                "telegram_chat_id": chat_id,
                "frequencia_minutos": freq
            })
            st.success("Salvo!")

    st.write("")
    if st.button("Recalcular Base de Dados"):
        with st.spinner("Processando..."):
            etl_silver.executar_etl_silver()
            etl_gold.executar_etl_gold()
        st.success("Otimizado!")

# ==========================================
# ÁREA PRINCIPAL
# ==========================================
tab_dashboard, tab_alertas = st.tabs(["Dashboard", "Alertas de Preço"])

# ABA 1: DASHBOARD
with tab_dashboard:
    df_gold = db.carregar_dados_gold()
    
    if not df_gold.empty:
        lista_termos = sorted(df_gold['termo_busca'].unique())
        
        index_padrao = 0
        if 'ultimo_produto_visto' in st.session_state and st.session_state['ultimo_produto_visto'] in lista_termos:
             index_padrao = lista_termos.index(st.session_state['ultimo_produto_visto'])

        termo_selecionado = st.selectbox("Selecione o Produto:", lista_termos, index=index_padrao)
        st.session_state['ultimo_produto_visto'] = termo_selecionado
        
        if termo_selecionado:
            dados_gold_termo = df_gold[df_gold['termo_busca'] == termo_selecionado].sort_values('data_coleta')
            dados_silver_termo = db.carregar_dados_silver(termo_selecionado)
            
            # Filtro Lateral aplicado aqui
            if not dados_silver_termo.empty:
                dados_silver_termo = dados_silver_termo[
                    (dados_silver_termo['preco_final'] >= min_val) & 
                    (dados_silver_termo['preco_final'] <= max_val)
                ]

            if not dados_gold_termo.empty:
                registro_atual = dados_gold_termo.iloc[-1]
                custo_bd = registro_atual.get('preco_custo')
                custo_bd = float(custo_bd) if custo_bd else 0.0
                
                ui.renderizar_kpis(registro_atual, custo_bd, float(registro_atual['preco_minimo']))
                ui.renderizar_graficos(dados_gold_termo, dados_silver_termo, custo_bd)
    else:
        st.info("Utilize a barra lateral para iniciar uma busca.")

# ABA 2: ALERTAS
with tab_alertas:
    st.header("Gerenciamento de Alertas")
    
    df_gold_alertas = db.carregar_dados_gold()
    
    if not df_gold_alertas.empty:
        produtos_unicos = df_gold_alertas.sort_values('data_coleta').drop_duplicates('termo_busca', keep='last')
        
        with st.container(border=True):
            st.subheader("Configurar Novo Alvo")
            col_a, col_b, col_c = st.columns([2, 1, 1])
            
            with col_a:
                prod_alvo = st.selectbox("Produto", produtos_unicos['termo_busca'])
                custo_atual_db = produtos_unicos[produtos_unicos['termo_busca'] == prod_alvo]['preco_custo'].values[0]
                if pd.isna(custo_atual_db): custo_atual_db = 0.0

            with col_b:
                novo_custo = st.number_input("Preço Alvo (R$)", value=float(custo_atual_db), step=50.0)
            
            with col_c:
                st.write("")
                st.write("")
                if st.button("Salvar Alvo"):
                    db.atualizar_custo_gold(prod_alvo, novo_custo)
                    st.toast("Preço salvo!")
                    time.sleep(1)
                    st.rerun()

        st.subheader("Lista de Alertas Ativos")
        df_display = produtos_unicos[['termo_busca', 'preco_custo', 'preco_minimo', 'loja_mais_barata']].copy()
        df_display.columns = ['Produto', 'Preço Alvo', 'Melhor Preço', 'Loja']
        
        st.dataframe(
            df_display, 
            width=None,
            use_container_width=True, 
            column_config={
                "Preço Alvo": st.column_config.NumberColumn(format="R$ %.2f"),
                "Melhor Preço": st.column_config.NumberColumn(format="R$ %.2f")
            },
            hide_index=True
        )