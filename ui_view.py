import streamlit as st
import plotly.express as px
from utils import analisar_competitividade

def renderizar_kpis(registro_atual, custo_bd, menor_preco_mercado):
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

def renderizar_graficos(dados_gold_termo, dados_silver_termo, custo_bd):
    tab1, tab2 = st.tabs(["🦅 Visão Estratégica", "📋 Dados Detalhados"])

    with tab1:
        c_g1, c_g2 = st.columns([2, 1])
        with c_g1:
            st.subheader("📉 Histórico de Preços")
            fig_tunnel = px.area(dados_gold_termo, x='data_coleta', y='preco_minimo', markers=True)
            if custo_bd: fig_tunnel.add_hline(y=custo_bd, line_dash="dot", line_color="red", annotation_text="Custo")
            st.plotly_chart(fig_tunnel, use_container_width=True)
        
        with c_g2:
            st.subheader("🏆 Share of Buy Box")
            df_share = dados_gold_termo['loja_mais_barata'].value_counts().reset_index()
            st.plotly_chart(px.pie(df_share, values='count', names='loja_mais_barata', hole=0.4), use_container_width=True)

        st.divider()
        c_g3, c_g4 = st.columns(2)
        
        with c_g3:
            st.subheader("📦 Dispersão (Hoje)")
            if not dados_silver_termo.empty:
                fig_box = px.box(dados_silver_termo, x="preco_final", points="all", hover_data=["concorrente"])
                if custo_bd: fig_box.add_vline(x=custo_bd, line_color="red")
                st.plotly_chart(fig_box, use_container_width=True)
        
        with c_g4:
            st.subheader("⚔️ Ranking Médio")
            if not dados_silver_termo.empty:
                df_agg = dados_silver_termo.groupby('concorrente')['preco_final'].mean().reset_index().sort_values('preco_final')
                st.plotly_chart(px.bar(df_agg, x='preco_final', y='concorrente', orientation='h', text_auto='.2s'), use_container_width=True)

    with tab2:
        st.dataframe(dados_silver_termo, use_container_width=True)