# 🔍 Analisador de Contratos LLM RAG

Sistema de análise de contratos usando Large Language Models (LLM) e Retrieval-Augmented Generation (RAG) para análise inteligente de documentos contratuais, com foco em contratos de operadoras de fibra óptica.

## 🎯 Funcionalidades

- **Upload de Documentos**: Suporte para PDF, DOCX e TXT
- **Consultas em Linguagem Natural**: Faça perguntas sobre o contrato
- **Análise Automática**: Identificação de cláusulas importantes
- **Foco em Contratos de Operadoras**:
  - ⏱️ Tempos de SLA
  - 🔌 Quilometragem de fibra óptica
  - 💰 Valores de multa
  - 📅 Prazos de contrato

## 🏗️ Arquitetura

```
├── models/                 # Modelos de dados
│   ├── document.py        # Modelos de documento
│   └── contract_analysis.py # Modelos de análise
├── services/              # Serviços de negócio
│   └── base_service.py    # Classe base para serviços
├── utils/                 # Utilitários
│   └── file_utils.py      # Utilitários de arquivo
├── uploads/               # Arquivos enviados
├── chroma_db/            # Banco de dados vetorial
├── config.py             # Configurações
├── app.py                # Interface Streamlit
└── requirements.txt      # Dependências
```

## 🚀 Instalação e Configuração

### 1. Clone e Configure o Ambiente

```bash
# Instalar dependências e configurar
python setup.py
```

### 2. Configure a API OpenAI

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e adicione sua chave
OPENAI_API_KEY=sua_chave_aqui
```

### 3. Execute a Aplicação

```bash
streamlit run app.py
```

## 📋 Modelos de Dados

### Document
- ID único, nome do arquivo, tipo, tamanho
- Status de processamento
- Conteúdo de texto extraído
- IDs de vetores para busca semântica

### ContractAnalysis
- Cláusulas identificadas por tipo
- Níveis de risco
- Termos específicos extraídos
- Flags de risco e recomendações

### QuerySession
- Histórico de perguntas e respostas
- Fontes citadas com localização
- Pontuação de confiança

## 🔧 Configurações

Principais configurações no `config.py`:

- **OPENAI_MODEL**: Modelo LLM (padrão: gpt-4)
- **MAX_FILE_SIZE_MB**: Tamanho máximo de arquivo (padrão: 50MB)
- **CHUNK_SIZE**: Tamanho dos chunks para vetorização (padrão: 1000)
- **CONTRACT_TYPES**: Tipos de cláusulas a identificar

## 📊 Status do Desenvolvimento

- ✅ **Tarefa 1**: Estrutura do projeto e interfaces principais
- ⏳ **Próximas**: Processamento de documentos, sistema RAG, interface completa

## 🛠️ Tecnologias

- **Frontend**: Streamlit
- **LLM**: OpenAI GPT-4
- **Vector DB**: ChromaDB
- **Processamento**: PyPDF2, python-docx
- **Embeddings**: OpenAI text-embedding-ada-002

## 📝 Próximos Passos

1. Implementar validação e upload de arquivos
2. Criar pipeline de extração de texto
3. Integrar banco de dados vetorial
4. Desenvolver sistema de consultas RAG
5. Adicionar análise automática de cláusulas
6. Implementar interface completa

## 🤝 Contribuição

Este projeto segue a metodologia de desenvolvimento orientado por especificações. Consulte os arquivos em `.kiro/specs/llm-rag-contract-analyzer/` para detalhes sobre requisitos, design e tarefas.