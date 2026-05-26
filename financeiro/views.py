import os
from google import genai
import numpy as np  # ◄ Import da biblioteca matemática para cálculo de vetores
from google.genai import types  # Caso precise de tipos futuramente
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Pessoa, Classificacao, MovimentoContas, ParcelaContas
from uuid import uuid4

class ConsultaRAGView(APIView):
    def post(self, request):
        pergunta = request.data.get('pergunta', '')
        metodo = request.data.get('metodo', 'simples')  # 'simples' ou 'embeddings'

        if not pergunta:
            return Response({"error": "A pergunta não pode estar vazia."}, status=status.HTTP_400_BAD_REQUEST)

        # Inicialização do Gemini
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            client = genai.Client(api_key=api_key)
        except Exception as e:
            return Response({"error": f"Falha ao inicializar o cliente Gemini: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Buscamos os dados do banco UMA VEZ para que ambos os métodos possam utilizar
        try:
            movimentos = list(MovimentoContas.objects.all().order_by('-id')[:20])
        except Exception as e:
            return Response({
                "error": f"Erro ao consultar a tabela MovimentoContas. Verifique se as colunas existem. Detalhe: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not movimentos:
            return Response({"resposta": "Nenhum registro de movimentação financeira foi localizado no banco de dados atualmente."}, status=status.HTTP_200_OK)

        contexto_banco = ""

        # =========================================================================
        # ABORDAGEM 1: RAG SIMPLES (Busca de Metadados Textuais via SQL)
        # =========================================================================
        if metodo == 'simples':
            contexto_banco = "DADOS ATUAIS DO SISTEMA FINANCEIRO:\n"
            for mov in movimentos[:10]:
                if hasattr(mov, 'pessoa') and mov.pessoa:
                    nome_fornecedor = getattr(mov.pessoa, 'nome_razao_social', getattr(mov.pessoa, 'nome', 'Fornecedor Anônimo'))
                else:
                    nome_fornecedor = "Não identificado"

                num_nota = getattr(mov, 'numero_nota', 'S/N')
                val_total = getattr(mov, 'valor_total', '0.00')
                tipo_mov = getattr(mov, 'tipo', 'A PAGAR')

                contexto_banco += f"- Nota: {num_nota} | Fornecedor: {nome_fornecedor} | Valor Total: R$ {val_total} | Tipo: {tipo_mov}\n"

        # =========================================================================
        # ABORDAGEM 2: RAG EMBEDDINGS (Busca Semântica Avançada) 🚀
        # =========================================================================
        elif metodo == 'embeddings':
            try:
                # 1. Gerar o vetor matemático para a PERGUNTA do usuário
                query_embedding_response = client.models.embed_content(
                    model='gemini-embedding-001',  # ◄ ALTERE AQUI
                    contents=pergunta
                )
                vector_pergunta = np.array(query_embedding_response.embeddings[0].values)

                trechos_e_scores = []

                # 2. Varrer os registros do PostgreSQL, gerando o texto descritivo e o vetor de cada um
                for mov in movimentos:
                    if hasattr(mov, 'pessoa') and mov.pessoa:
                        nome_fornecedor = getattr(mov.pessoa, 'nome_razao_social', getattr(mov.pessoa, 'nome', 'Não Identificado'))
                    else:
                        nome_fornecedor = "Não identificado"

                    num_nota = getattr(mov, 'numero_nota', 'S/N')
                    val_total = getattr(mov, 'valor_total', '0.00')
                    tipo_mov = getattr(mov, 'tipo', 'A PAGAR')
                    dt_emissao = getattr(mov, 'data_emissao', 'Não informada')

                    texto_nota = (
                        f"Nota Fiscal Número: {num_nota}. Fornecedor Emitente: {nome_fornecedor}. "
                        f"Valor Total da Operação: R$ {val_total}. Classificação do tipo de movimento: {tipo_mov}. "
                        f"Data de Emissão do Documento: {dt_emissao}."
                    )

                    # Gera o embedding para o texto desta nota específica
                    nota_embedding_response = client.models.embed_content(
                        model='gemini-embedding-001',  # ◄ ALTERE AQUI TAMBÉM
                        contents=texto_nota
                    )
                    vector_nota = np.array(nota_embedding_response.embeddings[0].values)

                    # 3. Calcular a Similaridade de Cosseno (Proximidade vetorial)
                    dot_product = np.dot(vector_pergunta, vector_nota)
                    norm_pergunta = np.linalg.norm(vector_pergunta)
                    norm_nota = np.linalg.norm(vector_nota)

                    similarity = dot_product / (norm_pergunta * norm_nota) if (norm_pergunta * norm_nota) > 0 else 0

                    trechos_e_scores.append((similarity, texto_nota))

                # 4. Ordenar do maior score para o menor e isolar os 3 melhores contextos
                trechos_e_scores.sort(key=lambda x: x[0], reverse=True)
                melhores_contextos = [trecho for score, trecho in trechos_e_scores[:3]]

                contexto_banco = "CONTEXTO SEMÂNTICO SELECIONADO POR PROXIMIDADE VETORIAL:\n" + "\n".join(melhores_contextos)

            except Exception as e:
                return Response({"error": f"Erro no pipeline de Embeddings: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({"error": "Método de consulta inválido."}, status=status.HTTP_400_BAD_REQUEST)

        # =========================================================================
        # PROMPT DE GERAÇÃO FINAL (Processa a resposta para AMBOS os métodos)
        # =========================================================================
        prompt_sistema = (
            "Você é um analista financeiro sênior e auditor de contas corporativas. "
            "Baseando-se estritamente no contexto dos dados reais do banco fornecidos abaixo, "
            "responda à pergunta do usuário de forma altamente profissional, encorpada e formal. "
            "Formate valores em Reais (R$) e datas adequadamente. Se os dados fornecidos não contiverem "
            "a resposta para a pergunta, informe formalmente que o registro específico não foi localizado na base atual.\n\n"
            f"CONTEXTO DOS DADOS DO BANCO:\n{contexto_banco}\n\n"
            f"PERGUNTA DO USUÁRIO: {pergunta}"
        )

        try:
            # Chamada oficial para o modelo do Gemini consolidada para os dois métodos
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt_sistema,
            )
            return Response({"resposta": response.text}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Erro na API do Gemini durante a geração: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)