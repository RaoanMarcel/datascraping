
def analisar_competitividade(meu_custo, menor_preco_mercado):
    """
    Analisa se o preço de mercado é perigoso para o seu negócio.
    Retorna um dicionário com: status, cor e mensagem.
    """
    if not meu_custo or meu_custo <= 0:
        return None

    diferenca = menor_preco_mercado - meu_custo
    margem_percentual = (diferenca / meu_custo) * 100

    resultado = {}

    if diferenca < 0:
        resultado['status'] = "CRÍTICO"
        resultado['cor'] = "red"
        resultado['icone'] = "🚨"
        resultado['msg'] = f"PERIGO: O mercado está vendendo R$ {abs(diferenca):.2f} abaixo do seu custo!"
    
    elif margem_percentual < 15: 
        resultado['status'] = "ALERTA"
        resultado['cor'] = "orange"
        resultado['icone'] = "⚠️"
        resultado['msg'] = f"Cuidado: Margem apertada ({margem_percentual:.1f}%). Concorrência acirrada."
    
    else:
        resultado['status'] = "OK"
        resultado['cor'] = "green"
        resultado['icone'] = "✅"
        resultado['msg'] = f"Oportunidade: Margem potencial de {margem_percentual:.1f}%."

    return resultado