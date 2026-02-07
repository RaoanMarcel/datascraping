# utils.py
import re
import unicodedata
import random
import time
from conf import USER_AGENTS # Importa nossas máscaras

def obter_headers_aleatorios():
    """Escolhe um User-Agent aleatório da lista"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }

def pausa_humana():
    """Dorme por um tempo aleatório entre 1.5 e 3.5 segundos"""
    tempo = random.uniform(1.5, 3.5)
    print(f"   (💤 Aguardando {tempo:.2f}s para parecer humano...)")
    time.sleep(tempo)

def limpar_preco(texto_sujo):
    """Sua função de limpar preço blindada"""
    if not texto_sujo: return 0.0
    try:
        texto = unicodedata.normalize("NFKD", str(texto_sujo))
        match = re.search(r'(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
        if match:
            numero_limpo = match.group(1).replace('.', '').replace(',', '.')
            return float(numero_limpo)
        return 0.0
    except:
        return 0.0