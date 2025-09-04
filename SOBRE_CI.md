# 🔄 CI/CD - Integração Contínua

## O que é o arquivo `.github/workflows/ci.yml`?

O arquivo `ci.yml` configura **GitHub Actions** para fazer **integração contínua** (CI). É um robozinho que roda automaticamente toda vez que você faz push ou pull request no GitHub!

## 🤖 O que o CI faz automaticamente:

### 1. **Testa o código** 
- Roda todos os testes automaticamente
- Verifica se nada quebrou

### 2. **Verifica qualidade do código**
- **Black**: Formata o código Python
- **isort**: Organiza os imports
- **flake8**: Encontra erros de estilo

### 3. **Ambiente limpo**
- Testa em Ubuntu Linux
- Python 3.11
- Instala dependências do zero

## 🚀 Como funciona:

```
Você faz push → GitHub Actions → Roda testes → ✅ ou ❌
```

## 📋 O que acontece no CI:

1. **Checkout**: Baixa seu código
2. **Setup Python**: Instala Python 3.11
3. **Instala deps**: `pip install` das dependências
4. **Lint**: Verifica formatação do código
5. **Tests**: Roda `pytest` com SQLite

## 🔧 Configurações do CI:

- **Banco**: SQLite (mais rápido para testes)
- **Celery**: Modo "eager" (sem Redis)
- **Auth**: Bypass (sem JWT nos testes)

## ✅ Status do CI:

Depois que configurar o repositório no GitHub, você verá:
- ✅ **Verde**: Tudo funcionando
- ❌ **Vermelho**: Algum teste falhou
- 🟡 **Amarelo**: Rodando

## 🛠️ Como usar:

### Primeiro push:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### Pushs normais:
```bash
git add .
git commit -m "Nova funcionalidade"
git push
```

O CI vai rodar automaticamente! 🎉

## 📊 Vantagens:

- **Qualidade**: Código sempre testado
- **Segurança**: Nada vai quebrar em produção
- **Equipe**: Todo mundo vê se os testes passam
- **Automático**: Zero trabalho manual

## 🐛 Se o CI falhar:

1. Veja os logs no GitHub
2. Corrija o erro localmente
3. Teste com: `pytest -q`
4. Faça novo push

## 🎯 Comandos para testar localmente:

```bash
# Ativar ambiente
.venv\Scripts\activate.bat

# Instalar ferramentas de lint
pip install black isort flake8

# Formatar código
black backend/app
isort backend/app

# Verificar erros
flake8 backend/app

# Rodar testes
pytest -q
```

---

**💡 Resumo**: O CI é seu "assistente robótico" que testa tudo automaticamente no GitHub! 🤖✨
