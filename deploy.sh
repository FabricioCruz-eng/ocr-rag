#!/bin/bash

echo "🚀 Script de Deploy - Analisador de Contratos"
echo "============================================="

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "Copie .env.example para .env e configure suas variáveis"
    exit 1
fi

# Verificar se OPENAI_API_KEY está configurada
if ! grep -q "OPENAI_API_KEY=" .env; then
    echo "❌ OPENAI_API_KEY não configurada no .env"
    exit 1
fi

echo "✅ Configurações verificadas"

# Opções de deploy
echo ""
echo "Escolha uma opção de deploy:"
echo "1) Streamlit Cloud (Gratuito)"
echo "2) Railway (Recomendado)"
echo "3) Heroku"
echo "4) Local (Teste)"

read -p "Digite sua escolha (1-4): " choice

case $choice in
    1)
        echo "📋 Deploy no Streamlit Cloud:"
        echo "1. Suba seu código para GitHub"
        echo "2. Acesse https://share.streamlit.io"
        echo "3. Conecte seu repositório"
        echo "4. Configure OPENAI_API_KEY nas secrets"
        ;;
    2)
        echo "🚂 Deploy no Railway:"
        if ! command -v railway &> /dev/null; then
            echo "Instalando Railway CLI..."
            npm install -g @railway/cli
        fi
        railway login
        railway up
        ;;
    3)
        echo "🟣 Deploy no Heroku:"
        if ! command -v heroku &> /dev/null; then
            echo "❌ Heroku CLI não encontrado. Instale em: https://devcenter.heroku.com/articles/heroku-cli"
            exit 1
        fi
        heroku login
        read -p "Nome do app: " app_name
        heroku create $app_name
        heroku config:set OPENAI_API_KEY=$(grep OPENAI_API_KEY .env | cut -d '=' -f2)
        git push heroku main
        ;;
    4)
        echo "🏠 Executando localmente:"
        streamlit run app.py
        ;;
    *)
        echo "❌ Opção inválida"
        exit 1
        ;;
esac