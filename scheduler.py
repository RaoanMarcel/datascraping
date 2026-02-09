import time
import sys
import asyncio
import json
from datetime import datetime

# Importa módulos
import kabum
import pichau
import etl_silver
import etl_gold
import notifier
import db_functions as db

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def carregar_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        return {"frequencia_minutos": 30} # Padrão se der erro

def job_rastreamento():
    print(f"\n⏰ [AGENDA] Iniciando varredura: {datetime.now()}")
    
    df = db.carregar_dados_gold()
    if df.empty:
        print("⚠️ Nada para rastrear. Cadastre produtos no Dashboard.")
        return

    lista_produtos = df['termo_busca'].unique()
    
    for produto in lista_produtos:
        print(f"   🔎 Buscando: {produto}...")
        try:
            kabum.buscar_produtos(produto)
            pichau.buscar_produtos(produto)
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            
    print("⚙️ Atualizando Banco...")
    etl_silver.executar_etl_silver()
    etl_gold.executar_etl_gold()
    
    notifier.verificar_alertas()
    print(f"🏁 [AGENDA] Fim da rodada: {datetime.now()}")

# --- LOOP PRINCIPAL DINÂMICO ---
print("🤖 Robô Iniciado! Lendo configurações do Dashboard...")

while True:
    # 1. Executa o trabalho
    job_rastreamento()
    
    # 2. Lê quanto tempo deve esperar até a próxima (Lê do JSON)
    config = carregar_config()
    minutos_espera = int(config.get("frequencia_minutos", 30))
    
    print(f"💤 Dormindo por {minutos_espera} minutos...")
    
    # Dorme (multiplicado por 60 para virar segundos)
    time.sleep(minutos_espera * 60)