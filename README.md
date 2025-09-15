# Painel de Vendas

Sistema interativo para análise de vendas, upload de planilhas Excel/CSV, geração de recibos em PDF e cadastro manual de informações, com backend Python e Supabase como banco de dados.

## Funcionalidades
- Upload e visualização de planilhas de vendas (Excel/CSV)
- Geração de recibos/notas em PDF
- Painel interativo com gráficos
- Cadastro manual de clientes, produtos e vendas (armazenados no Supabase)
- Não armazena planilhas do usuário no banco de dados

## Requisitos
- Python 3.9+
- Conta gratuita no [Supabase](https://supabase.com/)

## Instalação
1. Clone o repositório:
   ```sh
   git clone <url-do-repo>
   cd painel-v2
   ```
2. Crie e ative o ambiente virtual:
   - **Windows (cmd):**
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **Linux/macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```
4. Configure o arquivo `.env` com as credenciais do Supabase (veja `.env.example`).
5. Execute o script SQL no Supabase Dashboard:
   - Acesse o [Supabase Dashboard](https://app.supabase.com)
   - Vá para SQL Editor
   - Execute o conteúdo do arquivo `supabase_tables.sql`

## Como rodar o projeto
1. **Opção 1 - Ativar ambiente virtual primeiro:**
   ```cmd
   .venv\Scripts\activate
   python -m streamlit run app.py
   ```

2. **Opção 2 - Usar caminho completo (sempre funciona):**
   ```cmd
   ".venv\Scripts\python.exe" -m streamlit run app.py
   ```
3. Acesse o painel pelo navegador, normalmente em [http://localhost:8501](http://localhost:8501)

## Observações
- As planilhas enviadas não são salvas no banco de dados, apenas processadas localmente.
- Apenas cadastros manuais (clientes, produtos, vendas) são enviados ao Supabase.
- Para produção, recomenda-se configurar variáveis de ambiente seguras e usar HTTPS.

## Estrutura do projeto
```
├── app.py                # App principal Streamlit
├── core/                 # Lógica de negócio e integração
│   ├── supabase_client.py   # Configuração de conexão com Supabase
│   ├── supabase_db.py       # Funções CRUD (usuários, vendas, autenticação)
│   ├── invoice.py           # Geração de PDFs com ReportLab
│   └── parser.py            # Detecção e padronização de colunas Excel/CSV
├── sample_data/          # Modelos e exemplos de planilha
│   ├── modelo_vendas.xlsx   # Planilha vazia para o usuário preencher
│   └── dados_exemplo.xlsx   # Planilha com dados prontos para testar
├── uploads/              # PDFs gerados temporariamente
├── requirements.txt      # Dependências Python
├── database_final.sql    # Script para criar tabelas no Supabase
├── .env.example          # Exemplo de configuração de ambiente
└── .gitignore            # Arquivos ignorados pelo Git
```

### 📄 **Detalhes dos arquivos principais:**

**`core/invoice.py`** - Geração de PDFs profissionais
- Cria recibos/notas fiscais em PDF usando ReportLab
- Inclui cabeçalho, itens detalhados e total
- Formato A4 com layout profissional

**`core/parser.py`** - Inteligência para planilhas
- Detecta automaticamente colunas em Excel/CSV
- Mapeia nomes como "produto", "qtd", "preço" para formato padrão
- Suporta diferentes formatos de data e nomenclaturas
- Torna o sistema compatível com várias planilhas

**`core/supabase_db.py`** - Operações do banco
- Autenticação de usuários
- CRUD completo para vendas, clientes e usuários
- Funções seguras que protegem dados por usuário

**`sample_data/`** - Arquivos para download
- `modelo_vendas.xlsx`: Planilha vazia para preencher
- `dados_exemplo.xlsx`: Dados prontos para testar o sistema

---
Projeto desenvolvido com Python, Streamlit e Supabase.
