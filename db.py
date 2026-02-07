# -*- coding: utf-8 -*-
from curl_cffi import requests # A biblioteca que burla o bloqueio 403
from bs4 import BeautifulSoup
import psycopg2
import re
import sys

# --- CONFIGURAÇÕES DO BANCO ---
DB_CONFIG = {
    "host": "localhost",
    "database": "estoque_inteligente",
    "user": "postgres",
    "password": "admin", # <--- LEMBRE DE ATUALIZAR A SENHA
    "port": "5432"
}

def salvar_no_banco(dados):
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO bronze.precos_concorrentes (produto_nome, preco_raw, concorrente, url_fonte)
                    VALUES (%(nome)s, %(preco)s, %(concorrente)s, %(url)s);
                """, dados)
                conn.commit()
                print(f"[SUCESSO] {dados['nome']} salvo no banco!")
    except Exception as e:
        print(f"[ERRO BANCO] {e}")

def raspar_pichau_blindado(url):
    print(f"--- Acessando via Chrome Simulado: {url} ---")
    
    try:
        # O SEGREDOS: impersonate="chrome" faz o site achar que somos um navegador real
        response = requests.get(url, impersonate="chrome", timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 1. TÍTULO
            titulo = soup.find('h1')
            titulo_texto = titulo.get_text().strip() if titulo else "Titulo Nao Encontrado"

            # 2. PREÇO (Busca por "à vista")
            preco_texto = None
            elemento_a_vista = soup.find(string=re.compile("à vista"))
            
            if elemento_a_vista:
                parent = elemento_a_vista.parent
                text_completo = parent.get_text()
                # Regex para pegar o R$ x.xxx,xx
                match = re.search(r'R\$\s*[\d\.]+(?:,\d{2})?', text_completo)
                if match:
                    preco_texto = match.group(0)

            if preco_texto:
                print(f"[ACHEI] Preço: {preco_texto}")
                salvar_no_banco({
                    "nome": titulo_texto,
                    "preco": preco_texto,
                    "concorrente": "Pichau",
                    "url": url
                })
            else:
                print("[AVISO] Página carregou, mas não achei o preço (O layout pode ser diferente).")
        
        else:
            print(f"[ERRO] O site ainda bloqueou com código: {response.status_code}")

    except Exception as e:
        print(f"[CRASH] Erro na execução: {e}")

if __name__ == "__main__":
    # Link da RTX 5060 que você mandou
    url = "https://www.pichau.com.br/placa-de-video-inno3d-geforce-rtx-5060-twin-x2-oc-v2-8gb-gddr7-128-bit-n50602-08d7x-195071n"
    raspar_pichau_blindado(url)