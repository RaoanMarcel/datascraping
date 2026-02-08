import streamlit as st
import plotly.express as px
import io # Necessário para criar o arquivo Excel na memória
from utils import analisar_competitividade

def renderizar_kpis(registro_atual, custo_bd, menor_preco_mercado, variacao_preco=0):
    # --- KPI CARDS ---
    c1, c2, c3, c4 = st.columns(4)
    
    # KPI 1: Menor Preço com Setinha de Tendência
    c1.metric(
        "Menor Preço", 
        f"R$ {menor_preco_mercado:,.2f}", 
        delta=f"{variacao_preco:,.2f}" if variacao_preco != 0 else None,
        delta_color="inverse" 
    )
    
    c2.metric("Média Mercado", f"R$ {registro_atual['preco_medio']:,.2f}")
    c3.metric("Loja Vencedora", registro_atual['loja_mais_barata'])
    
    str_custo = f"R$ {custo_bd:,.2f}" if (custo_bd and custo_bd > 0) else "Não definido"
    c4.metric("Meu Custo", str_custo)

    # --- ALERTA DE COMPETITIVIDADE ---
    if custo_bd and custo_bd > 0:
        analise = analisar_competitividade(float(custo_bd), menor_preco_mercado)
        if analise:
            st.markdown("---")
            if analise['status'] == "CRÍTICO":
                st.error(analise['msg'], icon="🚨")
            elif analise['status'] == "ALERTA":
                st.warning(analise['msg'], icon="⚠️")
            else:
                st.success(analise['msg'], icon="✅")
    
    st.markdown("---")

def renderizar_graficos(dados_gold_termo, dados_silver_termo, custo_bd):
    tab1, tab2 = st.tabs(["Visão Estratégica", "Dados Detalhados"])

    with tab1:
        c_g1, c_g2 = st.columns([2, 1])
        
        with c_g1:
            st.markdown("#### Evolução do Menor Preço")
            fig_tunnel = px.area(
                dados_gold_termo, 
                x='data_coleta', 
                y='preco_minimo', 
                markers=True,
                color_discrete_sequence=["#8A2BE2"] 
            )
            if custo_bd: 
                fig_tunnel.add_hline(y=custo_bd, line_dash="dot", line_color="#FF4B4B", annotation_text="Custo")
            
            fig_tunnel.update_layout(yaxis_title="Preço (R$)")
            st.plotly_chart(fig_tunnel, use_container_width=True)
        
        with c_g2:
            st.markdown("#### Dominância (Buy Box)")
            if 'loja_mais_barata' in dados_gold_termo.columns:
                df_share = dados_gold_termo['loja_mais_barata'].value_counts().reset_index()
                fig_pie = px.pie(
                    df_share, 
                    values='count', 
                    names='loja_mais_barata', 
                    hole=0.5,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        c_g3, c_g4 = st.columns(2)
        
        with c_g3:
            st.markdown("#### Dispersão de Preços (Hoje)")
            if not dados_silver_termo.empty:
                fig_box = px.box(
                    dados_silver_termo, 
                    x="preco_final", 
                    points="all", 
                    hover_data=["concorrente"],
                    color_discrete_sequence=["#00CC96"]
                )
                if custo_bd: 
                    fig_box.add_vline(x=custo_bd, line_color="#FF4B4B", annotation_text="Custo")
                st.plotly_chart(fig_box, use_container_width=True)
        
        with c_g4:
            st.markdown("#### Quem está mais barato?")
            if not dados_silver_termo.empty:
                df_agg = dados_silver_termo.groupby('concorrente')['preco_final'].mean().reset_index().sort_values('preco_final')
                
                fig_bar = px.bar(
                    df_agg, 
                    x='preco_final', 
                    y='concorrente', 
                    orientation='h', 
                    text_auto='.2s',
                    color='preco_final',
                    color_continuous_scale='Bluyl'
                )
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        # --- EXPORTAR DADOS (EXCEL) ---
        col_dl1, col_dl2 = st.columns([1, 3])
        with col_dl1:
            # Cria um buffer na memória para o arquivo Excel
            buffer = io.BytesIO()
            
            # Escreve o DataFrame no buffer usando engine 'openpyxl' ou 'xlsxwriter'
            # O Pandas geralmente detecta automático.
            with st.spinner("Gerando Excel..."):
                try:
                    dados_silver_termo.to_excel(buffer, index=False, engine='openpyxl')
                    buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Baixar Excel (.xlsx)",
                        data=buffer,
                        file_name='relatorio_mercado.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    )
                except Exception as e:
                    st.error(f"Erro ao gerar Excel. Instale o openpyxl (pip install openpyxl). Erro: {e}")

        # --- TABELA INTERATIVA COM LINKS ---
        # Corrigido para 'url_fonte' que é o nome real no banco
        st.dataframe(
            dados_silver_termo, 
            use_container_width=True,
            column_config={
                "url_fonte": st.column_config.LinkColumn(
                    "Visitar Loja",           # Título da Coluna
                    display_text="Confira 🔗" # Texto clicável
                ),
                "preco_final": st.column_config.NumberColumn(
                    "Preço Final",
                    format="R$ %.2f"
                ),
                "data_processamento": st.column_config.DatetimeColumn(
                    "Data Coleta",
                    format="DD/MM/YYYY HH:mm"
                )
            }
        )