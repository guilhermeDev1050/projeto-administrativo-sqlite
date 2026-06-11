from django.shortcuts import render
from django.conf import settings
import json

# Importação do Agente de Extração
from .agents.agent1.agent_extracaodados import Agent1


def interpretar_pdf(request):

    if request.method == 'POST':
        arquivo_pdf = request.FILES.get('file_pdf')

        # --- 1. Validações ---
        # Verifica se a chave da API do extrator está configurada no settings.py
        if not getattr(settings, 'GEMINI_EXTRATOR_API_KEY', None):
            return render(request, 'interpreter/extrair_dados.html', {
                'error': "ERRO FATAL: Chave API do Gemini para o Extrator não configurada. Verifique settings.py."
            })

        # Verifica se um arquivo foi enviado e se é um PDF
        if not arquivo_pdf or not arquivo_pdf.name.lower().endswith('.pdf'):
            return render(request, 'interpreter/extrair_dados.html', {
                'error': 'Nenhum arquivo válido (PDF) foi enviado.'
            })

        # --- 2. Processamento com Agente ---
        try:
            # Inicializa o agente
            agent1 = Agent1()
            # Chama a função de extração, passando o arquivo
            resultado = agent1.extract_pdf_data(arquivo_pdf)

            if resultado['success']:
                dados_extraidos = resultado['dados_extraidos']

                # Remove e armazena o dicionário de CLASSIFICAÇÃO/Classificação
                classificacao = dados_extraidos.pop('CLASSIFICAÇÃO', None) or dados_extraidos.pop('Classificação', None)

                # DEBUG
                print("\n=== DADOS EXTRAÍDOS (Console do Servidor) ===")
                print(json.dumps(dados_extraidos, indent=2, ensure_ascii=False))
                print("===================================================\n")

                # Formata os dados para string JSON para enviar ao template
                dados_formatados = json.dumps(dados_extraidos, indent=2, ensure_ascii=False)

                # Retorna os dados para o template
                return render(request, 'interpreter/extrair_dados.html', {
                    'dados_extraidos': dados_formatados,
                    'classificacao': classificacao
                })
            else:
                return render(request, 'interpreter/extrair_dados.html', {
                    'error': resultado.get('error', 'Erro desconhecido na extração')
                })

        except Exception as e:
            return render(request, 'interpreter/extrair_dados.html', {
                'error': f'Erro fatal ao processar PDF: {str(e)}'
            })

    # --- 3. Carregamento Inicial (GET) ---
    return render(request, 'interpreter/extrair_dados.html')
