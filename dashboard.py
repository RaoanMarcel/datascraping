import streamlit as st
import pandas as pd
import psycopg2
from db import DB_CONFIG

# 1. Configuração da Página
st.set_page_config(page_title="Monitor de Preços GPU", layout="wide")

# 2. Conexão e Cache (Para não travar o banco)
@st.cache_data
def carregar_dados():
    conn = psycopg2.connect(**DB_CONFIG)
    # Query otimizada com apelidos (aliases) para evitar aquele erro anterior
    query = """
    SELECT 
        b.produto_nome, 
        s.preco_final, 
        s.concorrente, 
        b.url_fonte as link, 
        s.data_processamento 
    FROM silver.precos_limpos AS s
    JOIN bronze.precos_concorrentes AS b ON s.id_bronze = b.id
    ORDER BY s.preco_final ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# 3. Interface Principal
st.title("🦅 Monitor de Mercado: Hardware")
st.markdown("---")

# Carrega os dados iniciais
df = carregar_dados()

# 4. Barra Lateral de Filtros (A Mágica acontece aqui)
st.sidebar.header("🔍 Filtros Avançados")

# --- Filtro de Texto (O que você pediu!) ---
busca_usuario = st.sidebar.text_input("Buscar Modelo (ex: Gigabyte, 4060, Asus)", "")

# --- Filtro de Loja ---
todas_lojas = df['concorrente'].unique()
lojas_selecionadas = st.sidebar.multiselect("Lojas", todas_lojas, default=todas_lojas)

# --- Filtro de Preço ---
preco_max_db = float(df['preco_final'].max())
preco_min_db = float(df['preco_final'].min())

range_preco = st.sidebar.slider(
    "Faixa de Preço", 
    min_value=preco_min_db, 
    max_value=preco_max_db, 
    value=(preco_min_db, preco_max_db) # Tupla: (min, max)
)

# 5. Aplicando a Lógica de Filtragem
# Primeiro, filtra pelas lojas e preço
df_filtrado = df[
    (df['concorrente'].isin(lojas_selecionadas)) & 
    (df['preco_final'] >= range_preco[0]) & 
    (df['preco_final'] <= range_preco[1])
]

# Depois, se o usuário digitou algo, filtra pelo texto
if busca_usuario:
    # A mágica: procura o texto dentro da coluna 'produto_nome', ignorando maiúsculas (case=False)
    df_filtrado = df_filtrado[df_filtrado['produto_nome'].str.contains(busca_usuario, case=False, na=False)]

# 6. Exibindo os Resultados
if not df_filtrado.empty:
    # KPIs Dinâmicos (Mudam conforme sua busca)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Itens Encontrados", len(df_filtrado))
    col1.metric("Menor Preço", f"R$ {df_filtrado['preco_final'].min():.2f}")
    col2.metric("Média da Busca", f"R$ {df_filtrado['preco_final'].mean():.2f}")
    col2.metric("Maior Preço", f"R$ {df_filtrado['preco_final'].max():.2f}")

    # Tabela Interativa
    st.subheader(f"Resultados para: {busca_usuario if busca_usuario else 'Todos os produtos'}")
    
    st.dataframe(
        df_filtrado[['produto_nome', 'preco_final', 'concorrente', 'link']],
        column_config={
            "produto_nome": st.column_config.TextColumn("Produto", width="medium"),
            "preco_final": st.column_config.NumberColumn("Preço (R$)", format="R$ %.2f"),
            "link": st.column_config.LinkColumn("Link para Compra"),
            "concorrente": "Loja"
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Gráfico simples para comparar preços da busca atual
    st.markdown("### 📊 Comparativo de Preços")
    st.scatter_chart(df_filtrado, x="concorrente", y="preco_final", color="concorrente", size=100)

else:
    st.warning(f"Nenhum produto encontrado com o termo '{busca_usuario}'. Tente outro termo.")

# Botão de refresh
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()