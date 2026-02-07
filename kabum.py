# kabum.py
from curl_cffi import requests
from bs4 import BeautifulSoup
import db
import utils # Agora com headers aleatórios

def buscar(termo):
    print(f"--- [KABUM] Buscando: {termo} ---")
    url = f"https://www.kabum.com.br/busca/{termo.replace(' ', '-')}"
    
    # 1. Pega headers aleatórios
    headers_ninja = utils.obter_headers_aleatorios()

    try:
        # 2. Faz a requisição com os headers falsos
        response = requests.get(url, impersonate="chrome", headers=headers_ninja, timeout=20)
        
        # 3. Pausa para não parecer ataque DDoS
        utils.pausa_humana()

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ESTRATÉGIA GENÉRICA (BUSCAR LINKS COM /PRODUTO/)
        links = soup.find_all('a', href=True)
        
        count = 0
        urls_vistas = set()

        for link in links:
            href = link['href']
            texto = link.get_text(separator=" ", strip=True)
            
            # Filtro: Link de produto + Tem "R$"
            if "/produto/" in href and "R$" in texto:
                
                full_url = "https://www.kabum.com.br" + href
                if full_url in urls_vistas: continue
                
                preco = utils.limpar_preco(texto)
                if preco < 100: continue 
                
                # Tenta achar nome na imagem ou no texto
                nome = "Produto Kabum"
                img = link.find('img')
                if img and img.get('alt'):
                    nome = img.get('alt')
                else:
                    nome = texto.split("R$")[0].strip()[:100]

                db.salvar_preco({
                    "nome": nome,
                    "preco": preco,
                    "concorrente": "Kabum",
                    "url": full_url
                })
                urls_vistas.add(full_url)
                count += 1

        print(f"--- [KABUM] Sucesso: {count} itens encontrados. ---")

    except Exception as e:
        print(f"[KABUM ERRO] {e}")