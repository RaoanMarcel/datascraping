# app.py
import pichau
import kabum
from concurrent.futures import ThreadPoolExecutor

def iniciar_monitoramento_global(produto):
    print(f"\n🚀 INICIANDO MONITORAMENTO GLOBAL: {produto.upper()}\n")
    
    # Executa os dois ao mesmo tempo (Paralelismo)
    # Assim a busca na Pichau e Kabum rodam juntas, economizando tempo
    with ThreadPoolExecutor() as executor:
        executor.submit(pichau.buscar, produto)
        executor.submit(kabum.buscar, produto)

if __name__ == "__main__":
    termo = input("O que deseja buscar no mercado hoje? ")
    iniciar_monitoramento_global(termo)