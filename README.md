# 🔍 OCR RAG - Analisador de Contratos com IA

Sistema avançado de análise de contratos usando **OCR (Tesseract)**, **RAG (Retrieval-Augmented Generation)** e **LLM (Large Language Models)** para análise inteligente de documentos contratuais.

## 🎯 Funcionalidades

### 📄 Processamento de Documentos
- **Upload de múltiplos formatos**: PDF, DOCX, TXT
- **OCR avançado**: Extração de texto de imagens usando Tesseract
- **Suporte multilíngue**: Português e Inglês
- **Pré-processamento inteligente**: Melhoria automática de imagens para OCR

### 🤖 Análise Inteligente
- **Sistema RAG**: Busca semântica com vetores
- **LLM Integration**: Respostas contextuais usando GPT-4
- **Análise automática**: Identificação de cláusulas importantes
- **Extração de dados**: SLA, multas, prazos, fibra óptica

### 🔍 Busca Semântica
- **ChromaDB**: Banco de dados vetorial para busca eficiente
- **Embeddings OpenAI**: Vetorização de alta qualidade
- **Consultas em linguagem natural**: Faça perguntas sobre os contratos
- **Relevância contextual**: Respostas baseadas no conteúdo específico

## 🚀 Demo Online

**Aplicação em Produção**: [https://ocr-project-production.up.railway.app](https://ocr-project-production.up.railway.app)

## 🏗️ Arquitetura

```
├── app.py                     # Interface Streamlit principal
├── services/                  # Serviços de negócio
│   ├── document_service.py    # Gerenciamento de documentos
│   ├── text_extraction_service.py # OCR e extração de texto
│   ├── vector_service.py      # Sistema de vetores e embeddings
│   └── query_service.py       # Sistema RAG e consultas
├── models/                    # Modelos de dados
│   ├── document.py           # Modelos de documento
│   └── contract_analysis.py  # Modelos de análise
├── utils/                     # Utilitários
├── tests/                     # Testes automatizados
├── Dockerfile                # Container Docker com Tesseract
└── requirements.txt          # Dependências Python
```

## 🛠️ Tecnologias

### Backend
- **Python 3.11**: Linguagem principal
- **Streamlit**: Interface web interativa
- **OpenAI GPT-4**: Large Language Model
- **ChromaDB**: Banco de dados vetorial
- **Tesseract OCR**: Reconhecimento óptico de caracteres

### Processamento de Documentos
- **PyMuPDF**: Processamento avançado de PDFs
- **PyPDF2**: Fallback para PDFs
- **python-docx**: Documentos Word
- **Pillow**: Processamento de imagens
- **pytesseract**: Interface Python para Tesseract

### Deploy e Infraestrutura
- **Docker**: Containerização
- **Railway**: Plataforma de deploy
- **GitHub**: Controle de versão

## 🚀 Instalação e Configuração

### 1. Clone o Repositório
```bash
git clone https://github.com/FabricioCruz-eng/ocr-rag.git
cd ocr-rag
```

### 2. Configuração do Ambiente
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env e adicione sua chave OpenAI
```

### 3. Instalação do Tesseract

#### Windows:
1. Baixe o instalador: [Tesseract Windows](https://github.com/UB-Mannheim/tesseract/wiki)
2. Instale com suporte ao português
3. O projeto detecta automaticamente o caminho

#### Linux/Docker:
```bash
apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng
```

### 4. Executar Localmente
```bash
streamlit run app.py
```

Acesse: http://localhost:8501

## 🐳 Deploy com Docker

### Build da Imagem
```bash
docker build -t ocr-rag .
```

### Executar Container
```bash
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=sua_chave_aqui \
  ocr-rag
```

## ☁️ Deploy na Nuvem

### Railway (Recomendado)
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login e deploy
railway login
railway up

# Configurar variáveis
railway variables --set "OPENAI_API_KEY=sua_chave_aqui"
```

### Outras Plataformas
- **Heroku**: Use o `Procfile` incluído
- **Render**: Use o `render.yaml` incluído
- **DigitalOcean**: Use o `.do/app.yaml` incluído

## 📋 Configuração

### Variáveis de Ambiente
```env
# OpenAI Configuration
OPENAI_API_KEY=sua_chave_openai
OPENAI_MODEL=gpt-4

# Application Settings
MAX_FILE_SIZE_MB=50
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Database Settings
CHROMA_DB_PATH=./chroma_db
```

### Configuração do Streamlit
```toml
# .streamlit/config.toml
[server]
port = 8501
address = "localhost"
headless = false

[theme]
primaryColor = "#e9775d"
backgroundColor = "#ffffff"
```

## 🧪 Testes

### Executar Testes
```bash
# Teste do sistema de vetores
python test_vector_debug.py

# Teste do Tesseract OCR
python test_tesseract.py

# Testes unitários
python -m pytest tests/
```

## 📊 Funcionalidades Específicas

### Análise de Contratos de Operadoras
- **⏱️ Tempos de SLA**: Identificação automática de prazos
- **🔌 Fibra Óptica**: Extração de quilometragem e especificações
- **💰 Valores de Multa**: Identificação de penalidades
- **📅 Prazos de Contrato**: Duração e vigência
- **📄 Números de Contrato**: Identificação automática

### Sistema RAG Avançado
- **Busca Contextual**: Encontra informações relevantes
- **Respostas Inteligentes**: Combina múltiplas fontes
- **Pontuação de Confiança**: Avalia a qualidade das respostas
- **Citação de Fontes**: Mostra trechos específicos utilizados

## 🔧 Desenvolvimento

### Estrutura de Serviços
- **BaseService**: Classe base com logging e tratamento de erros
- **DocumentService**: Gerenciamento completo de documentos
- **TextExtractionService**: OCR e extração de texto
- **VectorService**: Embeddings e busca semântica
- **QueryService**: Sistema RAG e análise inteligente

### Modelos de Dados
- **Document**: Representação de documentos
- **DocumentSection**: Chunks de texto para vetorização
- **ContractAnalysis**: Análise específica de contratos
- **QuerySession**: Sessões de consulta e histórico

## 📈 Performance

### Otimizações Implementadas
- **Cache de embeddings**: Evita recálculos desnecessários
- **Processamento assíncrono**: Upload e processamento paralelos
- **Chunking inteligente**: Divisão otimizada de texto
- **Pré-processamento de imagens**: Melhora a precisão do OCR

### Métricas
- **Precisão OCR**: >95% em documentos de qualidade
- **Tempo de resposta**: <3s para consultas simples
- **Capacidade**: Até 50MB por documento
- **Throughput**: Múltiplos documentos simultâneos

## 🤝 Contribuição

### Como Contribuir
1. Fork o repositório
2. Crie uma branch para sua feature
3. Implemente as mudanças
4. Adicione testes
5. Envie um Pull Request

### Padrões de Código
- **PEP 8**: Estilo de código Python
- **Type Hints**: Tipagem estática
- **Docstrings**: Documentação de funções
- **Testes**: Cobertura mínima de 80%

## 📝 Changelog

### v1.0.0 (2025-08-03)
- ✅ Sistema OCR completo com Tesseract
- ✅ Integração RAG com ChromaDB
- ✅ Interface Streamlit responsiva
- ✅ Deploy automatizado no Railway
- ✅ Análise específica de contratos
- ✅ Suporte a múltiplos formatos
- ✅ Sistema de vetores otimizado

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

**Fabricio Cruz**
- Email: fabricio.cruz@claro.com.br
- GitHub: [@FabricioCruz-eng](https://github.com/FabricioCruz-eng)
- LinkedIn: [Fabricio Cruz](https://linkedin.com/in/fabricio-cruz-eng)

## 🙏 Agradecimentos

- **OpenAI**: Pela API GPT-4 e embeddings
- **Streamlit**: Pela framework de interface
- **ChromaDB**: Pelo banco de dados vetorial
- **Tesseract**: Pelo OCR open source
- **Railway**: Pela plataforma de deploy

---

**Copyright © 2025 Fabricio Cruz - Todos os direitos reservados**