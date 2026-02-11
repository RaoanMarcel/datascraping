import pichau
import kabum
import time
import terabyte
import mercadolivre

import streamlit as st
import subprocess
import sys
import os
import warnings
import asyncio
import json
import pandas as pd
import time
import plotly.express as px
import io 

def install_playwright():
    if "PLAYWRIGHT_INSTALLED" not in st.session_state:
        with st.spinner("Instalando navegador para coleta de dados..."):
            try:
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                subprocess.run([sys.executable, "-m", "playwright", "install-deps"], check=True)
                st.session_state["PLAYWRIGHT_INSTALLED"] = True
                st.success("Navegador instalado!")
            except Exception as e:
                st.error(f"Erro na instalação: {e}")

install_playwright()


def iniciar_monitoramento_global(produto):
    print(f"\n🚀 INICIANDO MONITORAMENTO DE DADOS: {produto.upper()}\n")
    
    kabum.buscar(produto)
    
    print("⏳ Trocando de loja...")
    time.sleep(2)
    
    pichau.buscar(produto)

    print("⏳ Trocando de loja...")
    time.sleep(2)

    terabyte.buscar_produtos(produto)

    print("⏳ Trocando de loja...")
    time.sleep(2)

    mercadolivre.buscar_produtos(produto)

if __name__ == "__main__":
    termo = input("O que deseja buscar no mercado hoje? ")
    iniciar_monitoramento_global(termo)