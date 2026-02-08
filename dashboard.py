import streamlit as st
import warnings
import asyncio
import sys
import re

# --- FIX DO WINDOWS ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# --- IMPORTAÇÕES MÓDULOS PRÓPRIOS ---
import kabum
import pichau
import etl_silver
import etl_gold
import db_functions as db
import ui_view as ui

# 1. Configuração da Página
st.set_page_config(page_title="Monitor Pro", layout="wide", page_icon="🦅")
warnings.filterwarnings('ignore') 

# --- CSS: ESTILO DOS INPUTS ---
st.markdown("""
<style>
    div[data-baseweb="input"] > div { padding: 8px 10px; }
    input[class] { font-size: 1.1rem; }
    label[data-baseweb="label"] { font-size: 0.95rem; font-weight: 600; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO AUXILIAR ---
def limpar_valor_moeda(valor_str):
    if not valor_str: return 0.0
    limpo = re.sub(r'[^\d,.]', '', str(valor_str))
    if ',' in limpo:
        limpo = limpo.replace('.', '').replace(',', '.')
    try: return float(limpo)
    except ValueError: return 0.0

# --- BARRA LATERAL (CONTROLE) ---
st.sidebar.title("Comando")
st.sidebar.markdown("---")

with st.sidebar.form(key='search_form'):
    st.markdown("### Nova Busca")
    
    novo_termo = st.text_input("Produto", placeholder="Ex: iPhone 15")
    
    custo_digitado = st.text_input("Preço de Custo", placeholder="0,00", help="Ex: 1500,00")
    preco_custo_input = limpar_valor_moeda(custo_digitado)
    
    st.markdown("### Lojas Alvo")
    c1, c2 = st.columns(2)
    with c1: check_kabum = st.checkbox("Kabum", value=True)
    with c2: check_pichau = st.checkbox("Pichau", value=True)
    
    st.markdown("---")
    submit_button = st.form_submit_button(label='Rastrear Agora')

# --- FILTROS DE VISUALIZAÇÃO ---
st.sidebar.markdown("### 🌪️ Filtros")
# Slider para limpar dados "sujos" (ex: acessórios baratos)
filtro_preco_min, filtro_preco_max = st.sidebar.slider(
    "Faixa de Preço (R$)",
    min_value=0.0,
    max_value=20000.0,
    value=(100.0, 20000.0), # Valor padrão ignora coisas abaixo de 100 reais
    step=50.0
)

# --- ADMIN TOOLS ---
with st.sidebar.expander("Admin Tools"):
    if st.button("Reprocessar Silver"):
        etl_silver.executar_etl_silver()
        st.toast("Silver OK", icon="✅")
    if st.button("Reprocessar Gold"):
        etl_gold.executar_etl_gold()
        st.toast("Gold OK", icon="✅")

# --- LÓGICA DE EXECUÇÃO ---
if 'ultimo_termo_buscado' not in st.session_state:
    st.session_state['ultimo_termo_buscado'] = None

if submit_button and novo_termo:
    st.session_state['ultimo_termo_buscado'] = novo_termo
    
    with st.status("Iniciando rastreio...", expanded=True) as status:
        if check_kabum:
            st.write("Consultando Kabum...")
            try: kabum.buscar_produtos(novo_termo)
            except Exception as e: st.error(f"Erro Kabum: {e}")
        
        if check_pichau:
            st.write("Consultando Pichau...")
            try: pichau.buscar_produtos(novo_termo)
            except Exception as e: st.error(f"Erro Pichau: {e}")

        st.write("Atualizando dados...")
        etl_silver.executar_etl_silver()
        etl_gold.executar_etl_gold()

        if preco_custo_input > 0:
            db.atualizar_custo_gold(novo_termo, preco_custo_input)

        status.update(label="Pronto!", state="complete", expanded=False)
    st.rerun()

# --- DASHBOARD VISUAL ---
st.title("Monitor de Competitividade")
df_gold = db.carregar_dados_gold()

if not df_gold.empty:
    lista_termos = sorted(df_gold['termo_busca'].unique())
    index_padrao = 0
    
    if st.session_state['ultimo_termo_buscado'] in lista_termos:
        index_padrao = lista_termos.index(st.session_state['ultimo_termo_buscado'])
    
    termo_selecionado = st.selectbox("Selecione o Produto:", lista_termos, index=index_padrao)

    if termo_selecionado:
        # 1. Carrega Dados
        dados_gold_termo = df_gold[df_gold['termo_busca'] == termo_selecionado].sort_values('data_coleta')
        dados_silver_termo = db.carregar_dados_silver(termo_selecionado)
        
        # 2. Aplica Filtro do Slider (Remove sujeira dos dados atuais)
        if not dados_silver_termo.empty:
            dados_silver_termo = dados_silver_termo[
                (dados_silver_termo['preco_final'] >= filtro_preco_min) & 
                (dados_silver_termo['preco_final'] <= filtro_preco_max)
            ]
        
        # 3. Prepara Métricas
        if not dados_gold_termo.empty:
            registro_atual = dados_gold_termo.iloc[-1]
            
            # Cálculo da Tendência (Atual - Anterior)
            variacao = 0.0
            if len(dados_gold_termo) > 1:
                registro_anterior = dados_gold_termo.iloc[-2]
                preco_atual = float(registro_atual['preco_minimo'])
                preco_ant = float(registro_anterior['preco_minimo'])
                variacao = preco_atual - preco_ant
            
            # Custo Seguro
            custo_bd = registro_atual.get('preco_custo')
            if custo_bd is None: custo_bd = 0.0
            else: custo_bd = float(custo_bd)
            
            menor_preco = float(registro_atual['preco_minimo'])

            # 4. Renderiza UI (Passando a variação calculada)
            ui.renderizar_kpis(registro_atual, custo_bd, menor_preco, variacao)
            
            # Verifica se sobrou dados após o filtro
            if dados_silver_termo.empty:
                st.warning(f"⚠️ Nenhum produto encontrado entre R$ {filtro_preco_min} e R$ {filtro_preco_max}. Ajuste o filtro na barra lateral.")
            else:
                ui.renderizar_graficos(dados_gold_termo, dados_silver_termo, custo_bd)
else:
    st.info("Utilize o menu lateral para iniciar.")