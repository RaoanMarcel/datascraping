import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from db import DB_CONFIG

# --- IMPORTAÇÃO DOS SEUS ROBÔS E ETLS ---
# O Streamlit vai rodar eles como se fosse você no terminal
import kabum
import pichau
import etl_silver
import etl_gold

st.set_page_config(page_title="Monitor de Preços Pro", layout="wide", page_icon="🦅")

# --- FUNÇÕES DE CARREGAMENTO DE DADOS ---
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
    # Se tiver termo, filtra. Se não, traz os últimos 100.
    if termo:
        query = f"""
        SELECT produto_nome, preco_final, concorrente, data_processamento 
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

# --- INTERFACE LATERAL (CONTROLE) ---
st.sidebar.title("🦅 Centro de Comando")
st.sidebar.markdown("---")

# Formulário de Busca (Isso substitui o app.py)
with st.sidebar.form(key='search_form'):
    st.markdown("### 🕵️ Nova Pesquisa")
    novo_termo = st.text_input("Produto para monitorar", placeholder="Ex: RTX 4060")
    submit_button = st.form_submit_button(label='🔍 Buscar na Web')

# --- LÓGICA DE EXECUÇÃO (O CÉREBRO) ---
if submit_button and novo_termo:
    st.toast(f"Iniciando busca por: {novo_termo}...", icon="🤖")
    
    # Barra de progresso para dar feedback visual
    progress_text = "Operação em andamento. Por favor, aguarde."
    my_bar = st.progress(0, text=progress_text)

    try:
        # 1. Roda Kabum
        my_bar.progress(10, text="Varrendo Kabum...")
        # AQUI CHAMAMOS A FUNÇÃO DO SEU ARQUIVO KABUM
        # Se seu arquivo não tem função e roda solto, teremos que adaptar.
        # Assumindo que você encapsulou em uma função 'buscar_produtos(termo)' ou similar.
        # Se não tiver função, o import executa o código, mas é perigoso.
        # Vou assumir que você criou uma função 'minha_busca_kabum' ou similar.
        # Vamos usar um hack para recarregar o módulo se necessário ou chamar a função.
        
        # MODO SEGURO: Chame as funções que você tem lá. 
        # Vou assumir que a lógica principal está acessível.
        kabum.buscar_produtos(novo_termo) # <--- CERTIFIQUE-SE QUE ESSA FUNÇÃO EXISTE NO KABUM.PY
        
        # 2. Roda Pichau
        my_bar.progress(40, text="Varrendo Pichau...")
        pichau.buscar_produtos(novo_termo) # <--- CERTIFIQUE-SE QUE ESSA FUNÇÃO EXISTE NO PICHAU.PY

        # 3. Roda ETL Silver
        my_bar.progress(70, text="Limpando dados (Silver)...")
        etl_silver.executar_etl_silver()

        # 4. Roda ETL Gold
        my_bar.progress(90, text="Gerando inteligência (Gold)...")
        etl_gold.executar_etl_gold()

        my_bar.progress(100, text="Concluído!")
        st.success(f"Dados de '{novo_termo}' atualizados com sucesso!")
        
    except Exception as e:
        st.error(f"Erro durante a execução: {e}")
        st.info("Dica: Verifique se seus arquivos kabum.py e pichau.py têm uma função chamada 'buscar_produtos(termo)'.")

# --- DASHBOARD VISUAL ---

# Carrega dados
df_gold = carregar_dados_gold()

st.title("📊 Monitor de Mercado")

# Seletor de visualização
lista_termos = df_gold['termo_busca'].unique()
termo_selecionado = st.selectbox("Selecione um Histórico:", lista_termos, index=0 if len(lista_termos) > 0 else None)

if termo_selecionado:
    # Filtra dados para o termo selecionado
    dados_gold_termo = df_gold[df_gold['termo_busca'] == termo_selecionado]
    dados_silver_termo = carregar_dados_silver(termo_selecionado)
    
    # KPIs
    ultimo_registro = dados_gold_termo.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Menor Preço Hoje", f"R$ {ultimo_registro['preco_minimo']}")
    col2.metric("Média de Mercado", f"R$ {ultimo_registro['preco_medio']}")
    col3.metric("Loja Vencedora", ultimo_registro['loja_mais_barata'])
    col4.metric("Itens Analisados", ultimo_registro['qtd_itens_encontrados'])

    # Abas para organizar a bagunça
    tab1, tab2 = st.tabs(["📈 Histórico (Gold)", "📋 Detalhes (Silver)"])

    with tab1:
        st.markdown("### Evolução de Preços")
        # Gráfico de Linha (Data vs Preço)
        fig = px.line(dados_gold_termo, x='data_coleta', y=['preco_minimo', 'preco_medio'], 
                      markers=True, title=f"Histórico: {termo_selecionado}")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Tabela Gold (Dados Consolidados)")
        st.dataframe(dados_gold_termo, use_container_width=True)

    with tab2:
        st.markdown(f"### Produtos Relacionados a '{termo_selecionado}'")
        st.markdown("Estes são os itens individuais que compõem a média acima.")
        
        # Filtro textual extra na tabela silver
        filtro_texto = st.text_input("Filtrar dentro da lista", "")
        if filtro_texto:
            dados_silver_termo = dados_silver_termo[dados_silver_termo['produto_nome'].str.contains(filtro_texto, case=False)]
            
        st.dataframe(
            dados_silver_termo, 
            use_container_width=True,
            column_config={
                "preco_final": st.column_config.NumberColumn("Preço", format="R$ %.2f")
            }
        )

else:
    st.info("👈 Use a barra lateral para fazer sua primeira busca ou aguarde carregar o histórico.")