"""
Setup script for LLM RAG Contract Analyzer
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        "uploads",
        "chroma_db",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Diretório criado: {directory}")

def check_env_file():
    """Check if .env file exists"""
    if not Path(".env").exists():
        print("⚠️  Arquivo .env não encontrado")
        print("📝 Copie .env.example para .env e configure sua chave da OpenAI")
        return False
    else:
        print("✅ Arquivo .env encontrado")
        return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Instalando dependências...")
    os.system("pip install -r requirements.txt")
    print("✅ Dependências instaladas")

def main():
    """Main setup function"""
    print("🚀 Configurando LLM RAG Contract Analyzer...")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Check environment file
    env_exists = check_env_file()
    
    # Install dependencies
    install_dependencies()
    
    print("=" * 50)
    print("✅ Setup concluído!")
    
    if not env_exists:
        print("\n⚠️  PRÓXIMOS PASSOS:")
        print("1. Copie .env.example para .env")
        print("2. Configure sua OPENAI_API_KEY no arquivo .env")
        print("3. Execute: streamlit run app.py")
    else:
        print("\n🎉 Pronto para usar!")
        print("Execute: streamlit run app.py")

if __name__ == "__main__":
    main()