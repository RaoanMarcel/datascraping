# -*- coding: utf-8 -*-
from curl_cffi import requests
from bs4 import BeautifulSoup
import psycopg2
import re
import os

# --- CONFIGURAÇÕES ---
DB_CONFIG = {
    "host": "localhost",
    "database": "estoque_inteligente",
    "user": "postgres",
    "password": "admin", # <--- CONFIRA SUA SENHA AQUI
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
                print(f"[SUCESSO] Preço {dados['preco']} salvo no banco!")
    except Exception as e:
        print(f"[ERRO BANCO] {e}")

def raspar_pichau_blindado(url):
    print(f"--- Acessando: {url} ---")
    
    try:
        # impersonate="chrome" é essencial para passar pelo Cloudflare
        response = requests.get(url, impersonate="chrome", timeout=15)
        
        # Se o site devolver erro 403, nem adianta continuar
        if response.status_code != 200:
            print(f"[ERRO HTTP] Código {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. TÍTULO
        titulo = soup.find('h1')
        titulo_texto = titulo.get_text().strip() if titulo else "Titulo Nao Encontrado"

        # 2. PREÇO (Lógica 'Shotgun' - Tenta pegar tudo)
        preco_encontrado = None
        
        # Estratégia: Procura onde está escrito "à vista" e pega os 100 caracteres antes dele
        # Isso resolve o problema de o preço estar em uma div irmã ou pai
        texto_pagina = soup.get_text(separator=" ", strip=True)
        
        # Regex poderosa: Procura "R$ (numeros)" que esteja perto de "à vista"
        # O padrão (?=.*à vista) olha pra frente pra ver se tem "à vista"
        match = re.search(r'R\$\s*[\d\.,]+(?=.*à vista)', texto_pagina, re.IGNORECASE)
        
        if match:
            preco_encontrado = match.group(0).strip()
        else:
            # Fallback: Tenta achar qualquer preço grande se a busca "à vista" falhar
            # Pega o primeiro padrão de preço que encontrar no HTML
            match_generico = re.search(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', texto_pagina)
            if match_generico:
                preco_encontrado = match_generico.group(0).strip()

        if preco_encontrado:
            print(f"[ACHEI] Preço: {preco_encontrado}")
            salvar_no_banco({
                "nome": titulo_texto,
                "preco": preco_encontrado,
                "concorrente": "Pichau",
                "url": url
            })
        else:
            print("[AVISO] Não achei o preço. Salvando HTML para análise...")
            # ISSO AQUI SALVA SUA PELE:
            with open("debug_pichau.html", "wb") as f:
                f.write(response.content)
            print(" -> Abra o arquivo 'debug_pichau.html' no navegador para ver o que houve.")

    except Exception as e:
        print(f"[CRASH] Erro na execução: {e}")

if __name__ == "__main__":
    # Link da RTX 5060
    url = "https://www.pichau.com.br/placa-de-video-inno3d-geforce-rtx-5060-twin-x2-oc-v2-8gb-gddr7-128-bit-n50602-08d7x-195071n"
    raspar_pichau_blindado(url)