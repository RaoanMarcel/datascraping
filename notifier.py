import requests
import json
import db_functions as db

# Função para ler o arquivo JSON
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
        print("⚠️ Telegram não configurado no Dashboard.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")

def verificar_alertas():
    print("🔔 Verificando oportunidades...")
    df = db.carregar_dados_gold()
    
    if df.empty:
        return

    ultima_data = df['data_coleta'].max()
    df_hoje = df[df['data_coleta'] == ultima_data]
    
    alertas = 0
    
    for _, row in df_hoje.iterrows():
        custo = row.get('preco_custo')
        preco_atual = float(row['preco_minimo'])
        produto = row['termo_busca']
        loja = row['loja_mais_barata']

        if custo and custo > 0:
            if preco_atual <= float(custo):
                diferenca = float(custo) - preco_atual
                
                msg = (
                    f"🚨 *OPORTUNIDADE DETECTADA!* 🚨\n\n"
                    f"📦 *{produto}*\n"
                    f"🛒 Loja: {loja}\n"
                    f"🔥 *Preço: R$ {preco_atual:,.2f}*\n"
                    f"🎯 Seu Alvo: R$ {custo:,.2f}\n"
                    f"📉 Economia: R$ {diferenca:,.2f}\n"
                )
                enviar_mensagem(msg)
                alertas += 1

    if alertas > 0:
        print(f"✅ {alertas} alertas enviados.")