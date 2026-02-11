import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import db

def buscar_produtos(termo):
    print(f"🔄 [MERCADO LIVRE] Iniciando busca: {termo}...")
    
    options = uc.ChromeOptions()
    options.add_argument("--no-first-run")
    options.add_argument("--window-position=-8000,0") 
    options.add_argument("--window-size=1920,1080")
    
    driver = uc.Chrome(options=options, version_main=144) 
    
    try:
        # Formata o termo para URL (ex: "rtx 4060" -> "rtx-4060")
        termo_url = termo.replace(" ", "-")
        url = f"https://lista.mercadolivre.com.br/{termo_url}"
        driver.get(url)
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ui-search-layout__item"))
            )
        except:
            print("⚠️ Demora no carregamento, tentando ler mesmo assim...")

        try:
            btn_cookie = driver.find_element(By.ID, "newCookieDisclaimerButton")
            btn_cookie.click()
        except: pass

        for i in range(1, 4):
            driver.execute_script(f"window.scrollTo(0, {i * 800});")
            time.sleep(1)

        cartoes = driver.find_elements(By.CLASS_NAME, "ui-search-layout__item")
        print(f"   -> Encontrei {len(cartoes)} itens no Mercado Livre.")
        
        count_sucesso = 0

        for cartao in cartoes:
            try:
                try:
                    tag_a = cartao.find_element(By.TAG_NAME, "a")
                    link = tag_a.get_attribute("href")
                    
                    # O título as vezes está num h2, as vezes no próprio link
                    try:
                        nome = cartao.find_element(By.TAG_NAME, "h2").text
                    except:
                        nome = tag_a.get_attribute("title") or tag_a.text
                except:
                    continue 

                if "O que você procurava" in nome: 
                    continue

                
                texto_completo = cartao.text

                precos_encontrados = re.findall(r'R\$\s?[\d\.,]+', texto_completo)
                
                if not precos_encontrados:
                    continue

                
                lista_valores = []
                for p_str in precos_encontrados:
                    nums = ''.join([c for c in p_str if c.isdigit() or c == ','])
                    if nums:
                        clean = nums.replace(',', '.')
                        if clean.count('.') > 1:
                            clean = clean.replace('.', '', clean.count('.') - 1)
                        valor = float(clean)
                        lista_valores.append(valor)

                if not lista_valores:
                    continue

                valores_validos = [v for v in lista_valores if v > 100]
                
                if not valores_validos:
                    continue

                preco_final = min(valores_validos)
                
                texto_preco_final = f"R$ {preco_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                db.salvar_preco({
                    "nome": nome[:150],
                    "preco": texto_preco_final,
                    "concorrente": "Mercado Livre",
                    "url": link,
                    "termo": termo
                })
                count_sucesso += 1

            except Exception as e:
                continue

        print(f"✅ [MERCADO LIVRE] Finalizado: {count_sucesso} itens salvos.")

    except Exception as e:
        print(f"❌ [MERCADO LIVRE] Erro: {e}")
    finally:
        try: driver.quit()
        except: pass

if __name__ == "__main__":
    buscar_produtos("rtx 4060")