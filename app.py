# app.py
import pichau
import kabum
import time

def iniciar_monitoramento_global(produto):
    print(f"\n🚀 INICIANDO MONITORAMENTO DE DADOS: {produto.upper()}\n")
    
    # Executa Kabum
    kabum.buscar(produto)
    
    print("⏳ Trocando de loja...")
    time.sleep(2)
    
    # Executa Pichau
    pichau.buscar(produto)

if __name__ == "__main__":
    termo = input("O que deseja buscar no mercado hoje? ")
    iniciar_monitoramento_global(termo)