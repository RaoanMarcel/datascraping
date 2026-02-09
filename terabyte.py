import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import db 

def buscar_produtos(termo):
    print(f"🔄 [TERABYTE] Iniciando busca blindada: {termo}...")
    
    options = uc.ChromeOptions()
    options.add_argument("--no-first-run")
    options.add_argument("--window-position=-12000,0") 
    options.add_argument("--window-size=1920,1080")
    
    driver = uc.Chrome(options=options, version_main=144) 
    
    try:
        url = f"https://www.terabyteshop.com.br/busca?str={termo}"
        driver.get(url)
        
        # Espera fixa para garantir scripts + Scroll
        time.sleep(4) 
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 2500);")
        time.sleep(1)

        # Pega todos os containers de produtos
        cartoes = driver.find_elements(By.CLASS_NAME, "product-item__content")
        
        count_sucesso = 0

        for cartao in cartoes:
            try:
                # 1. Nome e Link
                try:
                    tag_a = cartao.find_element(By.TAG_NAME, "a")
                    nome = tag_a.get_attribute("title")
                    if not nome: nome = tag_a.text.strip()
                    link = tag_a.get_attribute("href")
                except: continue

                # 2. Preço (Classe Oficial ou Regex)
                texto_preco = ""
                try:
                    elem_preco = cartao.find_element(By.CLASS_NAME, "product-item__new-price")
                    texto_preco = elem_preco.text.strip()
                except: pass 

                if not texto_preco:
                    # Plano B: Regex no texto todo do cartão
                    match = re.search(r'R\$\s?[\d\.,]+', cartao.text)
                    if match: texto_preco = match.group(0)
                
                if not texto_preco: continue

                # 3. Limpeza
                nums = ''.join([c for c in texto_preco if c.isdigit() or c == ','])
                preco_float = 0.0
                if nums:
                    clean = nums.replace(',', '.')
                    if clean.count('.') > 1: clean = clean.replace('.', '', clean.count('.') - 1)
                    preco_float = float(clean)

                # 4. Salvar
                if preco_float > 50:
                    db.salvar_preco({
                        "nome": nome[:150],
                        "preco": texto_preco,
                        "concorrente": "Terabyte",
                        "url": link,
                        "termo": termo
                    })
                    count_sucesso += 1

            except Exception:
                continue

        print(f"✅ [TERABYTE] Finalizado: {count_sucesso} itens salvos.")

    except Exception as e:
        print(f"❌ [TERABYTE] Erro: {e}")
    finally:
        try: driver.quit()
        except: pass