import streamlit as st
import warnings
import asyncio
import sys
import json
import os
import pandas as pd
import time
import plotly.express as px
import io 
import kabum
import pichau
import terabyte
import mercadolivre
import etl_silver
import etl_gold
import db_functions as db

# Fix para loop de eventos no Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

st.set_page_config(page_title="Monitor Pro - Analytics", layout="wide", page_icon="📈")
warnings.filterwarnings('ignore') 

st.markdown("""
<style>
    div[data-testid="InputInstructions"] > span:nth-child(1) { display: none; }
    div[data-baseweb="input"] > div { padding: 8px 10px; }
    input[class] { font-size: 1.1rem; }
    label[data-baseweb="label"] { font-size: 0.9rem; font-weight: 600; margin-bottom: 5px; color: #444; }
    section[data-testid="stSidebar"] { padding-top: 20px; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00CC96; }
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

st.sidebar.title("📈 Monitor Pro v3.0")
st.sidebar.markdown("---")

st.sidebar.subheader("Nova Pesquisa")
novo_termo = st.sidebar.text_input("Produto", placeholder="Ex: RTX 4060")

st.sidebar.write("Fontes de Dados:")
c1, c2 = st.sidebar.columns(2)
check_kabum = c1.checkbox("Kabum", value=True)
check_pichau = c2.checkbox("Pichau", value=True)
c3, c4 = st.sidebar.columns(2)
check_tera = c3.checkbox("Terabyte", value=True)
check_ml = c4.checkbox("ML", value=True)

if st.sidebar.button("Iniciar Coleta", type="primary"):
    if novo_termo:
        st.session_state['ultimo_produto_visto'] = novo_termo
        status_box = st.sidebar.status("Processando dados...", expanded=True)
        
        if check_kabum:
            status_box.write("🔄 Consultando Kabum...")
            try: kabum.buscar_produtos(novo_termo)
            except Exception as e: status_box.error(f"Erro Kabum: {e}")
        
        if check_pichau:
            status_box.write("🔄 Consultando Pichau...")
            try: pichau.buscar_produtos(novo_termo)
            except Exception as e: status_box.error(f"Erro Pichau: {e}")

        if check_tera:
            status_box.write("🔄 Consultando Terabyte...")
            try: terabyte.buscar_produtos(novo_termo)
            except Exception as e: status_box.error(f"Erro Tera: {e}")

        if check_ml:
            status_box.write("🔄 Consultando Mercado Livre...")
            try: mercadolivre.buscar_produtos(novo_termo)
            except Exception as e: status_box.error(f"Erro ML: {e}")

        status_box.write("Consolidando base (ETL)...")
        etl_silver.executar_etl_silver()
        etl_gold.executar_etl_gold()
        
        status_box.update(label="Processo Finalizado!", state="complete", expanded=False)
        time.sleep(1)
        st.rerun()
    else:
        st.sidebar.warning("Insira um termo para pesquisa.")

st.sidebar.markdown("---")

st.sidebar.subheader("Filtros de Dados")
min_val, max_val = st.sidebar.slider("Faixa de Preço (R$)", 0.0, 20000.0, (100.0, 20000.0))

st.sidebar.markdown("---")

with st.sidebar.expander("Configurações do Sistema"):
    config_atual = carregar_config()
    with st.form("admin_form"):
        st.markdown("**Notificações (Telegram)**")
        token = st.text_input("Bot Token", value=config_atual.get("telegram_token", ""), type="password")
        chat_id = st.text_input("Chat ID", value=config_atual.get("telegram_chat_id", ""))
        
        st.markdown("---")
        st.markdown("**Agendamento**")
        freq = st.number_input("Intervalo (min)", value=int(config_atual.get("frequencia_minutos", 60)))
        
        if st.form_submit_button("Salvar Parâmetros"):
            salvar_config({
                "telegram_token": token,
                "telegram_chat_id": chat_id,
                "frequencia_minutos": freq
            })
            st.success("Configurações salvas!")

    st.write("")
    if st.button("🔔 Testar Alerta"):
        import notifier
        try:
            notifier.testar_conexao()
            st.success("Notificação de teste enviada!")
        except:
            st.error("Falha no envio. Verifique as credenciais.")

tab_dashboard, tab_alertas = st.tabs(["📊 Visão de Mercado", "🎯 Gestão de Precificação"])

with tab_dashboard:
    df_gold = db.carregar_dados_gold()
    
    if not df_gold.empty:
        lista_termos = sorted(df_gold['termo_busca'].unique())
        
        index_padrao = 0
        if 'ultimo_produto_visto' in st.session_state and st.session_state['ultimo_produto_visto'] in lista_termos:
             index_padrao = lista_termos.index(st.session_state['ultimo_produto_visto'])

        col_sel, col_kpi1, col_kpi2, col_kpi3 = st.columns([3, 1.5, 1.5, 1.5])
        
        with col_sel:
            termo_selecionado = st.selectbox("Selecione o Produto:", lista_termos, index=index_padrao)
            st.session_state['ultimo_produto_visto'] = termo_selecionado
        
        if termo_selecionado:
            dados_produto = df_gold[df_gold['termo_busca'] == termo_selecionado]
            registro_atual = dados_produto.sort_values('data_coleta').iloc[-1]
            df_historico_raw = db.carregar_dados_silver(termo_selecionado)
            
            if not df_historico_raw.empty:
                if 'data_processamento' in df_historico_raw.columns:
                    df_historico_raw = df_historico_raw.rename(columns={'data_processamento': 'data_coleta'})
                elif 'data_hora' in df_historico_raw.columns:
                    df_historico_raw = df_historico_raw.rename(columns={'data_hora': 'data_coleta'})

                if 'concorrente' in df_historico_raw.columns:
                    df_historico_raw = df_historico_raw.rename(columns={'concorrente': 'loja'})

                if 'produto_nome' in df_historico_raw.columns:
                    df_historico_raw = df_historico_raw.rename(columns={'produto_nome': 'nome_produto'})
                
                if 'data_coleta' not in df_historico_raw.columns:
                    st.error(f"⚠️ Erro Crítico: Coluna de data não encontrada. Colunas: {list(df_historico_raw.columns)}")
                    st.stop()
            
            menor_preco = float(registro_atual['preco_minimo'])
            loja_vencedora = registro_atual['loja_mais_barata']
            
            df_snapshot = pd.DataFrame()
            if not df_historico_raw.empty:
                ultima_data = df_historico_raw['data_coleta'].max()
                df_snapshot = df_historico_raw[df_historico_raw['data_coleta'] == ultima_data]
                if not df_snapshot.empty:
                    media_mercado = df_snapshot['preco_final'].mean()
                else:
                    media_mercado = menor_preco
            else:
                media_mercado = menor_preco
            
            with col_kpi1:
                st.metric("Melhor Preço Atual", f"R$ {menor_preco:,.2f}", delta=f"{loja_vencedora}")
            with col_kpi2:
                diff_media = menor_preco - media_mercado
                st.metric("Média de Mercado", f"R$ {media_mercado:,.2f}", delta=f"{diff_media:,.2f} vs Média", delta_color="inverse")
            with col_kpi3:
                st.metric("Amostragem", f"{len(df_historico_raw)}", "Registros")

            st.markdown("---")

            if not df_historico_raw.empty:
                df_historico = df_historico_raw.copy()
                df_historico = df_historico[
                    (df_historico['preco_final'] >= min_val) & 
                    (df_historico['preco_final'] <= max_val)
                ]
                df_historico['data_coleta'] = pd.to_datetime(df_historico['data_coleta'])
                df_historico = df_historico.sort_values('data_coleta')

                st.subheader(f"📈 Evolução de Preços: {termo_selecionado}")
                fig_line = px.line(
                    df_historico, 
                    x="data_coleta", 
                    y="preco_final", 
                    color="loja",              
                    markers=True,              
                    labels={"preco_final": "Preço (R$)", "data_coleta": "Data/Hora", "loja": "Fonte"},
                    height=400
                )
                fig_line.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_line, use_container_width=True)

                st.markdown("### 🔎 Detalhamento")
                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    st.caption("Comparativo Atual (Menor Preço por Loja)")
                    if not df_snapshot.empty:
                        df_snap_filtered = df_snapshot[
                            (df_snapshot['preco_final'] >= min_val) & 
                            (df_snapshot['preco_final'] <= max_val)
                        ]
                        
                        if not df_snap_filtered.empty:
                            df_agrupado = df_snap_filtered.groupby('loja')['preco_final'].min().reset_index()
                            
                            fig_bar = px.bar(
                                df_agrupado,
                                x="loja",
                                y="preco_final",
                                color="loja",
                                text="preco_final",
                                labels={"preco_final": "Preço (R$)", "loja": "Fonte"}
                            )
                            fig_bar.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
                            fig_bar.update_layout(showlegend=False, height=350)
                            st.plotly_chart(fig_bar, use_container_width=True)
                        else:
                            st.warning("Nenhum dado na faixa selecionada.")
                    else:
                        st.write("Sem dados recentes.")

                with col_g2:
                    st.caption("Dispersão e Volatilidade")
                    fig_box = px.box(
                        df_historico,
                        x="loja",
                        y="preco_final",
                        color="loja",
                        points="all",
                        labels={"preco_final": "Preço (R$)", "loja": "Fonte"}
                    )
                    fig_box.update_layout(showlegend=False, height=350)
                    st.plotly_chart(fig_box, use_container_width=True)

                st.markdown("---")

                with st.expander("📄 Dados Analíticos e Exportação", expanded=False):
                    cols_to_show = ['data_coleta', 'nome_produto', 'loja', 'preco_final']
                    cols_present = [c for c in cols_to_show if c in df_historico.columns]
                    
                    df_export = df_historico[cols_present].sort_values('data_coleta', ascending=False)
                    
                    st.dataframe(
                        df_export,
                        use_container_width=True,
                        column_config={
                            "preco_final": st.column_config.NumberColumn(format="R$ %.2f"),
                            "data_coleta": st.column_config.DatetimeColumn(format="DD/MM HH:mm")
                        }
                    )
                    
                    col_dl1, col_dl2 = st.columns([1, 4])
                    with col_dl1:
                        try:
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                                df_export.to_excel(writer, index=False, sheet_name='Dados')
                                worksheet = writer.sheets['Dados']
                                worksheet.set_column('A:D', 20)
                            
                            st.download_button(
                                label="📥 Download Relatório (.xlsx)",
                                data=buffer.getvalue(),
                                file_name=f"analise_{termo_selecionado}.xlsx",
                                mime="application/vnd.ms-excel"
                            )
                        except ModuleNotFoundError:
                            st.error("Instale o xlsxwriter: pip install xlsxwriter")
            else:
                st.warning("Base de dados insuficiente para análise.")
    else:
        st.info("Utilize o menu lateral para iniciar a coleta.")

with tab_alertas:
    st.header("Análise de Margem e Competitividade")
    st.info("Defina seu custo ou preço alvo para análise de posicionamento de mercado.")
    
    df_gold_alertas = db.carregar_dados_gold()
    
    if not df_gold_alertas.empty:
        produtos_unicos = df_gold_alertas.sort_values('data_coleta').drop_duplicates('termo_busca', keep='last')
        
        with st.container(border=True):
            st.subheader("Parâmetros de Custo/Venda")
            col_prod, col_price, col_actions = st.columns([2, 1, 1.5])
            
            with col_prod:
                prod_alvo = st.selectbox("Item do Inventário", produtos_unicos['termo_busca'])
                dados_prod = produtos_unicos[produtos_unicos['termo_busca'] == prod_alvo]
                meu_preco_atual = dados_prod['preco_custo'].values[0]
                if pd.isna(meu_preco_atual): meu_preco_atual = 0.0

            with col_price:
                novo_preco = st.number_input("Meu Preço (R$)", value=float(meu_preco_atual), step=50.0)
            
            with col_actions:
                st.write("") 
                st.write("") 
                if st.button("💾 Salvar Parâmetros", use_container_width=True):
                    db.atualizar_custo_gold(prod_alvo, novo_preco)
                    st.toast("Parâmetros atualizados com sucesso!")
                    time.sleep(1)
                    st.rerun()

        st.subheader("Matriz de Competitividade")
        
        df_display = produtos_unicos.copy()
        df_display['diferenca'] = df_display['preco_custo'] - df_display['preco_minimo']
        
        def definir_status(row):
            meu_p = row['preco_custo']
            mercado_p = row['preco_minimo']
            
            if pd.isna(meu_p) or meu_p == 0: return "⚠️ Não Definido"
            
            diff = meu_p - mercado_p
            if diff > 0: 
                porcentagem = (diff / mercado_p) * 100
                if porcentagem > 10: return "🔴 Desvantagem Crítica"
                return "🟠 Acima do Mercado"
            elif diff < 0:
                if abs(diff) > (mercado_p * 0.15): return "🔵 Oportunidade/Margem"
                return "🟢 Competitivo"
            else: return "⚪ Neutro/Alinhado"

        df_display['Situação'] = df_display.apply(definir_status, axis=1)
        
        df_final = df_display[['termo_busca', 'preco_custo', 'preco_minimo', 'loja_mais_barata', 'Situação']].copy()
        df_final.columns = ['Produto', 'Referência Interna', 'Melhor Oferta', 'Líder Atual', 'Status Estratégico']
        
        st.dataframe(
            df_final, 
            use_container_width=True, 
            column_config={
                "Referência Interna": st.column_config.NumberColumn(format="R$ %.2f"),
                "Melhor Oferta": st.column_config.NumberColumn(format="R$ %.2f"),
            },
            hide_index=True
        )