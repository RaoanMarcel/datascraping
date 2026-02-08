from playwright.sync_api import sync_playwright
import db

# CORREÇÃO: O nome da função agora é buscar_produtos
def buscar_produtos(termo):
    print(f"🕵️‍♂️ [PICHAU] Iniciando busca invisível por: {termo}")
    
    with sync_playwright() as p:
        # headless=True com argumentos anti-bot
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"] 
        )
        
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        url = f"https://www.pichau.com.br/search?q={termo.replace(' ', '+')}"
        
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
            # Espera a rede acalmar (garante que os produtos carregaram)
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # Usando a lógica visual
            produtos = page.locator("a[href*='/']").all()
            
            count = 0
            urls_vistas = set() # Evita duplicatas na mesma rodada

            for prod in produtos:
                try:
                    texto_card = prod.inner_text()
                    
                    if "R$" in texto_card and len(texto_card) > 20:
                        linhas = texto_card.split('\n')
                        linhas_limpas = [l for l in linhas if "Frete" not in l and "Review" not in l and "%" not in l]
                        
                        if not linhas_limpas: continue

                        nome = max(linhas_limpas, key=len)
                        preco_raw = next((l for l in linhas if "R$" in l), None)
                        
                        href = prod.get_attribute("href")
                        full_url = "https://www.pichau.com.br" + href if href.startswith("/") else href

                        if full_url not in urls_vistas and preco_raw:
                            db.salvar_preco({
                                "nome": nome[:150],
                                "preco": preco_raw,
                                "concorrente": "Pichau",
                                "url": full_url,
                                "termo": termo
                            })
                            urls_vistas.add(full_url)
                            count += 1
                            if count >= 15: break # Limite de segurança

                except Exception:
                    continue

            print(f"✅ [PICHAU] Finalizado. {count} itens salvos.")

        except Exception as e:
            print(f"❌ [PICHAU] Erro Stealth: {e}")
        
        finally:
            browser.close()