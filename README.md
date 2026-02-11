Monitor Pro - Price Analytics & Dashboard

Monitor Pro é uma aplicação de Business Intelligence (BI) focada em monitoramento de preços de hardware e eletrônicos. O sistema realiza web scraping em grandes varejistas (Kabum, Pichau, Terabyte, Mercado Livre), processa os dados via pipeline ETL e apresenta insights estratégicos em um dashboard interativo.
Funcionalidades

    Coleta Multi-Fonte: Scrapers integrados para Kabum, Pichau, Terabyte e Mercado Livre.

    Pipeline ETL: Transformação de dados brutos (Raw) em dados analíticos (Gold).

    Dashboard Interativo:

        KPIs de menor preço e média de mercado.

        Histórico de preços (Time Series).

        Comparativo de lojas (Bar Chart & Boxplot).

    Gestão de Precificação: Matriz de competitividade comparando seu custo vs. mercado.

    Exportação: Relatórios em Excel (.xlsx) prontos para download.

    Alertas: Integração nativa com Telegram para notificações.

Arquitetura

O fluxo de dados segue uma abordagem simplificada de Lakehouse:
Snippet de código

graph LR
    A[Scrapers] -->|Dados Brutos| B(ETL Silver)
    B -->|Limpeza/Norm| C(ETL Gold)
    C -->|Agregação| D[Dashboard Streamlit]
    D -->|Análise| E[Usuário]
    D -->|Exportação| F[Excel]

Pré-requisitos

    Python 3.10 ou superior.

    Pip (Gerenciador de pacotes).

    Navegador Web (Chrome/Edge/Firefox).

Instalação

    Clone o repositório:
    Bash

    git clone https://github.com/seu-usuario/monitor-pro.git
    cd monitor-pro

    Crie um ambiente virtual (recomendado):
    Bash

    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate

    Instale as dependências:
    Bash

    pip install -r requirements.txt

    Nota: Certifique-se de que os drivers de navegador (se usar Selenium nos scrapers) estejam configurados ou instalados.

Como Executar

Para iniciar a aplicação web:
Bash

streamlit run app.py

O dashboard abrirá automaticamente em seu navegador padrão no endereço: http://localhost:8501.
Configuração
Arquivo config.json

O sistema cria automaticamente um arquivo config.json na raiz na primeira execução. Você pode editá-lo via interface (Menu Lateral > Configurações) ou manualmente:
JSON

{
    "telegram_token": "SEU_TOKEN_AQUI",
    "telegram_chat_id": "SEU_CHAT_ID",
    "frequencia_minutos": 60
}

Estrutura do Projeto
Plaintext

monitor-pro/
├── app.py              # Aplicação Principal (Streamlit)
├── config.json         # Configurações locais
├── db_functions.py     # Camada de Acesso a Dados (DAL)
├── etl_silver.py       # Tratamento e Higienização
├── etl_gold.py         # Regras de Negócio e Agregação
├── notifier.py         # Módulo de Notificações
├── requirements.txt    # Dependências do projeto
└── scrapers/           # Módulos de Coleta
    ├── kabum.py
    ├── pichau.py
    ├── terabyte.py
    └── mercadolivre.py

Contribuição

    Faça um Fork do projeto.

    Crie uma Branch para sua Feature (git checkout -b feature/NovaFeature).

    Faça o Commit (git commit -m 'Add some NovaFeature').

    Push para a Branch (git push origin feature/NovaFeature).

    Abra um Pull Request.
