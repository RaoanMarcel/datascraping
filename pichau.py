# pichau.py
from curl_cffi import requests
from bs4 import BeautifulSoup
import db
import utils

def buscar(termo):
    print(f"--- [PICHAU] Buscando: {termo} ---")
    url = f"https://www.pichau.com.br/search?q={termo.replace(' ', '+')}"
    
    headers_ninja = utils.obter_headers_aleatorios()
    
    try:
        response = requests.get(url, impersonate="chrome", headers=headers_ninja, timeout=20)
        utils.pausa_humana()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        links = soup.find_all('a', href=True)
        count = 0
        urls_vistas = set()

        for link in links:
            texto = link.get_text(separator=" ", strip=True)
            href = link['href']
            
            if "R$" in texto:
                full_url = href if href.startswith('http') else f"https://www.pichau.com.br{href}"
                if full_url in urls_vistas: continue
                
                preco = utils.limpar_preco(texto)
                if preco < 100: continue
                
                nome = texto.split("R$")[0].strip()[:100]
                if len(nome) < 5: continue

                db.salvar_preco({
                    "nome": nome,
                    "preco": preco,
                    "concorrente": "Pichau",
                    "url": full_url
                })
                urls_vistas.add(full_url)
                count += 1
                
        print(f"--- [PICHAU] Sucesso: {count} itens encontrados. ---")

    except Exception as e:
        print(f"[PICHAU ERRO] {e}")