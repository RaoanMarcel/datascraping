import requests
import json
import db_functions as db
import pandas as pd

def carregar_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def enviar_mensagem(texto):
    config = carregar_config()
    token = config.get("telegram_token")
    chat_id = config.get("telegram_chat_id")

    if not token or not chat_id:
        print(" Telegram não configurado.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = { "chat_id": chat_id, "text": texto, "parse_mode": "Markdown" }
    try: requests.post(url, json=payload)
    except Exception as e: print(f"❌ Erro Telegram: {e}")

def testar_conexao():
    enviar_mensagem("✅ **Sistema de Monitoramento Comercial Ativo!**")

def verificar_alertas():
    print("🔔 Analisando concorrência...")
    df = db.carregar_dados_gold()
    
    if df.empty: return

    # Pega apenas os dados mais recentes de cada produto
    df_analise = df.sort_values('data_coleta').drop_duplicates('termo_busca', keep='last')
    
    alertas_enviados = 0
    
    for _, row in df_analise.iterrows():
        produto = row['termo_busca']
        meu_preco = row.get('preco_custo') # "Meu Preço" no banco
        mercado_min = float(row['preco_minimo'])
        loja_rival = row['loja_mais_barata']

        # Se eu não defini meu preço, pular
        if not meu_preco or pd.isna(meu_preco) or meu_preco == 0:
            continue

        meu_preco = float(meu_preco)
        diff = meu_preco - mercado_min
        
        msg = ""

        # --- LÓGICA 1: DEFESA (Estou mais caro que o rival) ---
        if diff > 0:
            porcentagem_erro = (diff / mercado_min) * 100
            # Só avisa se eu estiver mais de 2% mais caro (pra evitar centavos)
            if porcentagem_erro > 2:
                msg = (
                    f" **ALERTA DE PERDA DE VENDAS** 🚨\n\n"
                    f" {produto}\n"
                    f" **Você está caro!**\n"
                    f" Seu Preço: R$ {meu_preco:,.2f}\n"
                    f" {loja_rival}: R$ {mercado_min:,.2f}\n\n"
                    f" **Sugestão:** Baixe R$ {diff:,.2f} para empatar."
                )

        # --- LÓGICA 2: ATAQUE (Estou muito barato / Deixando dinheiro na mesa) ---
        elif diff < 0:
            margem_sobra = abs(diff)
            # Se meu preço é muito menor (ex: > 10% abaixo do mercado)
            # Significa que posso aumentar meu preço e continuar sendo o mais barato
            if margem_sobra > (mercado_min * 0.10):
                msg = (
                    f" **OPORTUNIDADE DE LUCRO** \n\n"
                    f" {produto}\n"
                    f" **Você está muito barato!**\n"
                    f" Seu Preço: R$ {meu_preco:,.2f}\n"
                    f" Concorrência ({loja_rival}): R$ {mercado_min:,.2f}\n\n"
                    f" **Sugestão:** Você pode subir seu preço em até R$ {margem_sobra - 10:,.2f} e ainda será o líder!"
                )

        if msg:
            enviar_mensagem(msg)
            alertas_enviados += 1

    if alertas_enviados > 0:
        print(f"✅ {alertas_enviados} relatórios de estratégia enviados.")