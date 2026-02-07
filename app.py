# -*- coding: utf-8 -*-
from curl_cffi import requests
from bs4 import BeautifulSoup
import re
import db  # <--- AQUI ESTÁ A MÁGICA: Importamos nosso arquivo db.py

def raspar_pichau(url):
    print(f"--- Iniciando Scraping: {url} ---")
    
    try:
        # User-Agent simulado
        response = requests.get(url, impersonate="chrome", timeout=15)
        
        if response.status_code != 200:
            print(f"[ERRO HTTP] {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Extração do Título
        h1 = soup.find('h1')
        titulo = h1.get_text().strip() if h1 else "Sem Título"

        # 2. Extração do Preço (Lógica do 'à vista')
        texto_pagina = soup.get_text(separator=" ", strip=True)
        preco_texto = None
        
        # Procura R$ perto de 'à vista'
        match = re.search(r'R\$\s*[\d\.,]+(?=.*à vista)', texto_pagina, re.IGNORECASE)
        
        if match:
            preco_texto = match.group(0).strip()
        else:
            # Fallback genérico
            match_generico = re.search(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', texto_pagina)
            if match_generico:
                preco_texto = match_generico.group(0).strip()

        # 3. Entrega para o db.py salvar
        if preco_texto:
            print(f"[SCRAPER] Preço encontrado: {preco_texto}")
            
            pacote_dados = {
                "nome": titulo,
                "preco": preco_texto,
                "concorrente": "Pichau",
                "url": url
            }
            
            # Chama a função do outro arquivo
            db.salvar_preco(pacote_dados)
            
        else:
            print("[AVISO] Preço não encontrado.")

    except Exception as e:
        print(f"[ERRO GERAL] {e}")

if __name__ == "__main__":
    # Vamos testar com a RTX 4060 pra variar um pouco os dados no banco
    link = "https://www.pichau.com.br/placa-de-video-gigabyte-geforce-rtx-4060-eagle-oc-8gb-gddr6-128-bit-gv-n4060eagle-oc-8gd"
    raspar_pichau(link)