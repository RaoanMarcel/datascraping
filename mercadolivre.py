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
    options.add_argument("--window-position=-3000,0") 
    options.add_argument("--window-size=1920,1080")
    
    driver = uc.Chrome(options=options, version_main=144) 
    
    try:
        # Formata o termo para URL (ex: "rtx 4060" -> "rtx-4060")
        termo_url = termo.replace(" ", "-")
        url = f"https://lista.mercadolivre.com.br/{termo_url}"
        driver.get(url)
        
        # Espera carregar a lista
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ui-search-layout__item"))
            )
        except:
            print("⚠️ Demora no carregamento, tentando ler mesmo assim...")

        # Aceita cookies se aparecer (para limpar a tela)
        try:
            btn_cookie = driver.find_element(By.ID, "newCookieDisclaimerButton")
            btn_cookie.click()
        except: pass

        # Scroll suave para carregar imagens e preços dinâmicos
        for i in range(1, 4):
            driver.execute_script(f"window.scrollTo(0, {i * 800});")
            time.sleep(1)

        # 1. Pega os cards de produto (Layout de Lista ou Grade)
        cartoes = driver.find_elements(By.CLASS_NAME, "ui-search-layout__item")
        print(f"   -> Encontrei {len(cartoes)} itens no Mercado Livre.")
        
        count_sucesso = 0

        for cartao in cartoes:
            try:
                # --- A. Extração de Nome e Link ---
                try:
                    # Tenta pegar o link principal do card
                    tag_a = cartao.find_element(By.TAG_NAME, "a")
                    link = tag_a.get_attribute("href")
                    
                    # O título as vezes está num h2, as vezes no próprio link
                    try:
                        nome = cartao.find_element(By.TAG_NAME, "h2").text
                    except:
                        nome = tag_a.get_attribute("title") or tag_a.text
                except:
                    continue # Se não tem link ou nome, pula

                if "O que você procurava" in nome: # Ignora sugestões erradas
                    continue

                # --- B. Extração de Preço (REGEX BLINDADO) ---
                # O ML separa R$, Reais e Centavos em tags diferentes. 
                # O melhor jeito é pegar o texto bruto do bloco de preço.
                
                texto_completo = cartao.text
                
                # Regex procura: R$ seguido de espaco opcional, numeros, ponto ou virgula
                # Exemplo match: "R$ 1.500", "R$ 299,90"
                precos_encontrados = re.findall(r'R\$\s?[\d\.,]+', texto_completo)
                
                if not precos_encontrados:
                    continue

                # Lógica para pegar o preço certo:
                # O ML mostra: "R$ 2.000" (preço antigo riscado) "R$ 1.800" (preço atual)
                # E também: "12x R$ 150" (parcela)
                # Vamos pegar todos, converter para float e aplicar regras.
                
                lista_valores = []
                for p_str in precos_encontrados:
                    # Limpeza: R$ 1.200,50 -> 1200.50
                    nums = ''.join([c for c in p_str if c.isdigit() or c == ','])
                    if nums:
                        clean = nums.replace(',', '.')
                        if clean.count('.') > 1: # Remove ponto de milhar (1.200.50 -> 1200.50)
                            clean = clean.replace('.', '', clean.count('.') - 1)
                        valor = float(clean)
                        lista_valores.append(valor)

                if not lista_valores:
                    continue

                # REGRA DE OURO DO ML:
                # O preço real geralmente é o menor valor encontrado que seja > 50 reais
                # (para evitar pegar valor de parcela tipo R$ 15,00 ou juros)
                # Mas cuidado: as vezes o menor valor É a parcela.
                
                # Vamos assumir que o produto alvo custa mais que 100 reais
                valores_validos = [v for v in lista_valores if v > 100]
                
                if not valores_validos:
                    continue

                # Se houver múltiplos valores válidos (ex: preço antigo e novo),
                # o preço de venda é o menor entre eles (promoção) ou o único disponível.
                preco_final = min(valores_validos)
                
                # Formata para texto para salvar no banco
                texto_preco_final = f"R$ {preco_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                # --- C. Salvar ---
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