from playwright.sync_api import sync_playwright
import db

# CORREÇÃO: O nome da função agora é buscar_produtos
def buscar_produtos(termo):
    print(f"🕵️‍♂️ [KABUM] Iniciando busca invisível por: {termo}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        try:
            page.goto(f"https://www.kabum.com.br/busca/{termo.replace(' ', '-')}", timeout=60000)
            page.wait_for_selector("article", timeout=15000)
            
            produtos = page.query_selector_all("article")
            count = 0
            
            for prod in produtos:
                try:
                    # Quebra todo o texto do cartão em linhas
                    linhas = prod.inner_text().split('\n')
                    
                    # 1. Achar o Nome: Geralmente é a linha mais longa do cartão
                    # (Removemos linhas de frete/review para não confundir)
                    linhas_validas = [l for l in linhas if len(l) > 10 and "R$" not in l and "Review" not in l]
                    nome = max(linhas_validas, key=len) if linhas_validas else "Nome não detectado"

                    # 2. Achar o Preço: Procura a linha que tem "R$"
                    preco_raw = next((l for l in linhas if "R$" in l), None)
                    
                    # Pegar Link
                    link_el = prod.query_selector("a")
                    full_url = "https://www.kabum.com.br" + link_el.get_attribute("href") if link_el else ""

                    if preco_raw and nome:
                        db.salvar_preco({
                            "nome": nome[:150],
                            "preco": preco_raw, # Manda como TEXTO mesmo
                            "concorrente": "Kabum",
                            "url": full_url,
                            "termo": termo
                        })
                        count += 1
                        
                except Exception:
                    continue

            print(f"✅ [KABUM] Finalizado. {count} itens salvos.")

        except Exception as e:
            print(f"❌ [KABUM] Erro: {e}")
        finally:
            browser.close()