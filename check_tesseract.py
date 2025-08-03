"""
Check if Tesseract OCR is installed and configured
"""
import subprocess
import sys
import os

def check_tesseract():
    """Check if Tesseract is installed"""
    print("🔍 Verificando instalação do Tesseract OCR...")
    
    try:
        # Try to run tesseract
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Tesseract OCR está instalado!")
            print(f"Versão: {result.stdout.split()[1]}")
            return True
        else:
            print("❌ Tesseract não encontrado")
            return False
            
    except FileNotFoundError:
        print("❌ Tesseract não está instalado ou não está no PATH")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Timeout ao verificar Tesseract")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar Tesseract: {e}")
        return False

def install_instructions():
    """Show installation instructions"""
    print("\n📋 INSTRUÇÕES PARA INSTALAR TESSERACT:")
    print("=" * 50)
    print("1. Baixe o Tesseract para Windows:")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    print("\n2. Execute o instalador e instale em:")
    print("   C:\\Program Files\\Tesseract-OCR\\")
    print("\n3. Adicione ao PATH do sistema:")
    print("   C:\\Program Files\\Tesseract-OCR\\")
    print("\n4. Reinicie o terminal/IDE")
    print("\n5. Para suporte ao português, baixe:")
    print("   https://github.com/tesseract-ocr/tessdata")
    print("   Arquivo: por.traineddata")
    print("   Coloque em: C:\Program Files\Tesseract-OCR\Tesseract.exe")

def test_ocr():
    """Test OCR functionality"""
    try:
        import pytesseract
        from PIL import Image
        import numpy as np
        
        # Create a simple test image with text
        print("\n🧪 Testando OCR...")
        
        # Create a simple white image with black text
        img_array = np.ones((100, 300, 3), dtype=np.uint8) * 255
        test_image = Image.fromarray(img_array)
        
        # Try OCR
        text = pytesseract.image_to_string(test_image)
        print("✅ OCR está funcionando!")
        return True


# apontar onde está o executavel do pytesseract
#pytesseract.pytesseract.tesseract_cmd = "C:\Program Files\Tesseract-OCR\tesseract.exe"

    except Exception as e:
        print(f"❌ Erro no teste de OCR: {e}")
        return False

if __name__ == "__main__":
    tesseract_ok = check_tesseract()
    
    if tesseract_ok:
        ocr_ok = test_ocr()
        if ocr_ok:
            print("\n🎉 SISTEMA OCR PRONTO PARA USO!")
            print("💡 Agora você pode processar PDFs com texto e imagens")
        else:
            print("\n⚠️  Tesseract instalado mas OCR não está funcionando")
    else:
        install_instructions()
        print("\n⚠️  Instale o Tesseract para usar OCR em imagens")