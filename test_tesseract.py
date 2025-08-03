#!/usr/bin/env python3
"""
Teste do Tesseract OCR para verificar se está funcionando corretamente
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import tempfile

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_tesseract_basic():
    """Teste básico do Tesseract"""
    print("🔍 Testando Tesseract OCR...")
    
    try:
        # Verificar se o Tesseract está disponível
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract versão: {version}")
        
        # Verificar idiomas disponíveis
        langs = pytesseract.get_languages()
        print(f"✅ Idiomas disponíveis: {len(langs)} idiomas")
        
        if 'por' in langs:
            print("✅ Português disponível!")
        else:
            print("⚠️ Português não encontrado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste básico: {e}")
        return False

def test_tesseract_with_image():
    """Teste com uma imagem simples"""
    print("\n🖼️ Testando OCR com imagem...")
    
    try:
        # Criar uma imagem simples com texto
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Tentar usar uma fonte padrão
        try:
            # No Windows, usar fonte padrão
            font = ImageFont.load_default()
        except:
            font = None
        
        # Desenhar texto
        text = "Contrato SLA 24 horas"
        draw.text((10, 30), text, fill='black', font=font)
        
        # Salvar temporariamente
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            img.save(tmp_file.name)
            
            # Testar OCR
            extracted_text = pytesseract.image_to_string(img, lang='por')
            print(f"✅ Texto original: '{text}'")
            print(f"✅ Texto extraído: '{extracted_text.strip()}'")
            
            # Testar sem português
            extracted_text_eng = pytesseract.image_to_string(img)
            print(f"✅ Texto extraído (inglês): '{extracted_text_eng.strip()}'")
            
            # Limpar arquivo temporário
            os.unlink(tmp_file.name)
            
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste com imagem: {e}")
        return False

def test_tesseract_config():
    """Teste diferentes configurações do Tesseract"""
    print("\n⚙️ Testando configurações do Tesseract...")
    
    try:
        # Criar imagem de teste
        img = Image.new('RGB', (300, 50), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 15), "SLA 4 horas", fill='black')
        
        # Testar diferentes configurações
        configs = [
            ('Padrão', ''),
            ('PSM 6', '--psm 6'),
            ('PSM 6 + Português', '--psm 6 -l por'),
            ('OEM 3 + PSM 6', '--oem 3 --psm 6'),
            ('Completo', '--oem 3 --psm 6 -l por')
        ]
        
        for name, config in configs:
            try:
                text = pytesseract.image_to_string(img, config=config)
                print(f"✅ {name}: '{text.strip()}'")
            except Exception as e:
                print(f"❌ {name}: Erro - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de configurações: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Teste Completo do Tesseract OCR")
    print("=" * 50)
    
    # Verificar se o arquivo do Tesseract existe
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if not os.path.exists(tesseract_path):
        print(f"❌ Tesseract não encontrado em: {tesseract_path}")
        return False
    
    print(f"✅ Tesseract encontrado em: {tesseract_path}")
    
    # Executar testes
    tests = [
        test_tesseract_basic,
        test_tesseract_with_image,
        test_tesseract_config
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
            results.append(False)
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 Resumo dos Testes:")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ Todos os testes passaram! ({passed}/{total})")
        print("🎉 Tesseract está funcionando corretamente!")
    else:
        print(f"⚠️ {passed}/{total} testes passaram")
        print("🔧 Verifique a configuração do Tesseract")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)