from services.text_extraction_service import TextExtractionService

service = TextExtractionService()
test_text = """
CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE FIBRA ÓPTICA

Contrato nº DCT-NEO165-000210

CLÁUSULA 1 - DO OBJETO
O presente contrato tem por objeto a prestação de serviços de fibra óptica.

CLÁUSULA 2 - DO SLA
O SLA de atendimento será de 4 horas para incidentes críticos.
O prazo de 24 horas para incidentes de média prioridade.

CLÁUSULA 3 - DA EXTENSÃO
A extensão da fibra óptica será de 15,5 km.

CLÁUSULA 4 - DAS PENALIDADES
Em caso de descumprimento, será aplicada multa de R$ 5.000,00.

CLÁUSULA 5 - DA VIGÊNCIA
O contrato terá vigência de 24 meses.
"""

result = service.extract_contract_specific_info(test_text)
print("Resultado:", result["data"])