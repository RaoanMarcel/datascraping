import time
import sys
import asyncio
import json
from datetime import datetime

# --- IMPORTAÇÕES DAS LOJAS ---
import kabum
import pichau
import terabyte       # <--- Faltava esse
import mercadolivre   # <--- Faltava esse
import etl_silver
import etl_gold
import notifier
import db_functions as db

# Fix para Windows (Event Loop)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def carregar_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        return {"frequencia_minutos": 30} 

def job_rastreamento():
    print(f"\n⏰ [AGENDA] Iniciando varredura completa: {datetime.now()}")
    
    # Pega os produtos que você já cadastrou no Dashboard (tabela Gold)
    df = db.carregar_dados_gold()
    if df.empty:
        print("⚠️ Nada para rastrear. Cadastre produtos no Dashboard primeiro.")
        return

    # Lista única de termos para buscar
    lista_produtos = df['termo_busca'].unique()
    print(f"📋 Lista de tarefas: {lista_produtos}")
    
    for produto in lista_produtos:
        print(f"\n🔎 --- Buscando: {produto} ---")
        
        # KABUM
        try: kabum.buscar_produtos(produto)
        except Exception as e: print(f"  ❌ Erro Kabum: {e}")
        
        # PICHAU
        try: pichau.buscar_produtos(produto)
        except Exception as e: print(f"  ❌ Erro Pichau: {e}")

        # TERABYTE
        try: terabyte.buscar_produtos(produto)
        except Exception as e: print(f"  ❌ Erro Tera: {e}")

        # MERCADO LIVRE
        try: mercadolivre.buscar_produtos(produto)
        except Exception as e: print(f"  ❌ Erro ML: {e}")
            
    print("\n⚙️ Processando dados (ETL)...")
    etl_silver.executar_etl_silver()
    etl_gold.executar_etl_gold()
    
    print("🔔 Verificando Alertas...")
    notifier.verificar_alertas()
    
    print(f"🏁 [AGENDA] Fim da rodada: {datetime.now()}")

# --- LOOP PRINCIPAL ---
print("🤖 Robô 'Vigia Noturno' Iniciado!")

while True:
    job_rastreamento()
    
    # Lê configuração de tempo (permite mudar o tempo sem fechar o script)
    config = carregar_config()
    minutos_espera = int(config.get("frequencia_minutos", 60))
    
    print(f"💤 Dormindo por {minutos_espera} minutos... (Próxima: {minutos_espera}m)")
    time.sleep(minutos_espera * 60)