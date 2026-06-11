import json
import re
import PyPDF2
import google.generativeai as genai
from django.conf import settings


class Agent1:
    """Agente responsável pela extração de dados de PDFs"""

    def __init__(self):
        """Inicializa o agente com as configurações do Gemini"""
        genai.configure(api_key=settings.GEMINI_EXTRATOR_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def validar_dados_extraidos(self, dados):
        """Valida e sanitiza os dados extraídos da IA"""
        dados_validados = {}

        # 1. Fornecedor
        forn = dados.get('Fornecedor') or {}
        dados_validados['Fornecedor'] = {
            'Razão Social': str(forn.get('Razão Social', 'Não encontrado')),
            'Fantasia': str(forn.get('Fantasia', 'Não encontrado')),
            'CNPJ': str(forn.get('CNPJ', 'Não encontrado'))
        }

        # 2. Faturado
        fat = dados.get('Faturado') or {}
        nome_bruto = str(fat.get('Nome Completo', 'Não encontrado'))

        dados_validados['Faturado'] = {
            'Nome Completo': nome_bruto,
            'CPF': str(fat.get('CPF', 'Não encontrado')),
            'CNPJ': str(fat.get('CNPJ', 'Não encontrado'))
        }

        # 3. Demais campos estritamente na ordem exigida
        def _get_str(campo):
            v = dados.get(campo)
            return str(v).strip() if v else "Não encontrado"

        dados_validados["Número da Nota Fiscal"] = _get_str("Número da Nota Fiscal")
        dados_validados["Data de Emissão"] = _get_str("Data de Emissão")
        dados_validados["Descrição dos produtos"] = _get_str("Descrição dos produtos")
        dados_validados["Quantidade de Parcelas"] = _get_str("Quantidade de Parcelas")
        dados_validados["Data de Vencimento"] = _get_str("Data de Vencimento")
        dados_validados["ValorTotal"] = _get_str("ValorTotal")

        # 4. Classificação da DESPESA
        cls = dados.get('Classificação da DESPESA') or []
        classificacoes_prontas = []
        if isinstance(cls, list):
            for c in cls:
                if isinstance(c, dict):
                    classificacoes_prontas.append({
                        "categoria": str(c.get("categoria", "Não Classificado")),
                        "termos_utilizados": [str(t) for t in c.get("termos_utilizados", [])]
                    })
                else:
                    classificacoes_prontas.append({
                        "categoria": str(c),
                        "termos_utilizados": []
                    })
        elif isinstance(cls, str) and cls.strip():
            classificacoes_prontas.append({"categoria": cls, "termos_utilizados": []})
        else:
            classificacoes_prontas.append({"categoria": "Não Classificado", "termos_utilizados": []})

        dados_validados['Classificação da DESPESA'] = classificacoes_prontas

        # 5. Parcelas
        parcelas = dados.get('Parcelas')
        if isinstance(parcelas, list):
            dados_validados['Parcelas'] = parcelas
        else:
            dados_validados['Parcelas'] = []

        return dados_validados

    def processar_resposta_ia(self, response_text):
        """Processa resposta da IA com validação completa"""
        try:
            dados = json.loads(response_text)
            return self.validar_dados_extraidos(dados)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    dados = json.loads(json_match.group(0))
                    return self.validar_dados_extraidos(dados)
                except json.JSONDecodeError:
                    pass

        return {
            "Fornecedor": {
                "Razão Social": "Não encontrado",
                "Fantasia": "Não encontrado",
                "CNPJ": "Não encontrado"
            },
            "Faturado": {
                "Nome Completo": "Não encontrado",
                "CPF": "Não encontrado",
                "CNPJ": "Não encontrado"
            },
            "Número da Nota Fiscal": "Não encontrado",
            "Data de Emissão": "Não encontrado",
            "Descrição dos produtos": "Não encontrado",
            "Quantidade de Parcelas": "0",
            "Data de Vencimento": "Não encontrado",
            "ValorTotal": "0",
            "Classificação da DESPESA": [
                {
                    "categoria": "Não Classificado",
                    "termos_utilizados": []
                }
            ],
            "Parcelas": []
        }

    def extract_pdf_data(self, pdf_file):
        """Extrai dados de PDF usando as operações do agent1."""
        try:
            pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            texto = ""
            for pagina in pdf_reader.pages:
                texto += pagina.extract_text() or ""

            if not texto:
                return {'success': False, 'error': 'Não foi possível extrair texto do PDF'}

            prompt = f"""
Você é um sistema de IA avançado projetado para extrair informações de notas fiscais.
Por favor, extraia as seguintes informações do texto fornecido e retorne-as EXCLUSIVAMENTE em formato JSON:

{{
  "Fornecedor": {{
    "Razão Social": "",
    "Fantasia": "",
    "CNPJ": ""
  }},
  "Faturado": {{
    "Nome Completo": "Extraia o conteúdo do campo 'Nome/Razão Social' do destinatário",
    "CPF": "",
    "CNPJ": ""
  }},
  "Número da Nota Fiscal": "Extraia como TEXTO LITERAL, mantendo todos os zeros à esquerda (ex: '000.089.123')",
  "Data de Emissão": "",
  "Descrição dos produtos": "Faça um resumo ou lista dos itens",
  "Quantidade de Parcelas": "1",
  "Data de Vencimento": "",
  "ValorTotal": "",
  "Classificação da DESPESA": [
    {{
      "categoria": "",
      "termos_utilizados": [""]
    }}
  ],
  "Parcelas": [
    {{
      "numero": "1",
      "valor": "",
      "vencimento": ""
    }}
  ]
}}

REGRA:
- Faturado: O nome do faturado está localizado obrigatoriamente no campo 'Nome/Razão Social' do destinatário. Ignore informações de endereço (Rua, Av, Bairro) que venham na mesma linha ou logo abaixo.
- Faturado: Preencha o campo com a string EXATA e INTEGRAL da Razão Social/Nome. É PROIBIDO cortar ou resumir a string. Se ela contiver traços, setores ou sufixos, copie rigorosamente do mesmo jeito sem excluir absolutamente nada da marca. Remova apenas siglas intrusas do PDF caso venham coladas na frente (ex: 'ANTT').
- Data de Vencimento: não localizando, retorne a mesma data de emissão
- Descrição dos Produtos: não será necessário criar uma entidade PRODUTOS
- Quantidade de Parcelas: Neste momento vamos trabalhar com uma parcela, porém com estrutura para receber mais de uma parcela
- Classificação: Neste momento vamos trabalhar com uma classificação de DESPESA por registro, porém com estrutura para receber mais de uma classificação
- Valores Monetários: Todo valor (ValorTotal e Parcelas) DEVE ser formatado EXCLUSIVAMENTE no padrão brasileiro (ponto de milhar e vírgula de centavos: '3.254,07').
- Número da Nota Fiscal: Cuidado! O PyPDF costuma grudar a SÉRIE com o NÚMERO (ex: lendo '25SÉRIE000693983'). Extraia o NÚMERO com TODOS OS SEUS DÍGITOS EXATOS e POR COMPLETO (incluindo zeros à esquerda, ex: '000693983'), removendo apenas a Série se grudada.
- Faturado: O 'Nome Completo' pode vir falhado grudado à sigla do campo anterior (ex: 'ANTTOLLYVER OTTOBONI' que significa 'ANTT' + 'OLLYVER OTTOBONI'). Limpe o texto separando e extraindo APENAS o nome real da pessoa (ex: 'OLLYVER OTTOBONI') SEM excluir caracteres próprios do primeiro nome. Lembre-se: 'ANTONIO BORGES 39' é rua (endereço), não pessoa!
- Número da Nota Fiscal: Cuidado! O PyPDF costuma grudar a SÉRIE da nota com o NÚMERO (ex: lendo '25SÉRIE693983' ou '25693983'). O Número da Nota Fiscal NÃO inclui a Série. Em casos assim, extraia APENAS o número da nota propriamente dito (ex: '693983'). Extraia o número EXATAMENTE como aparece no documento, como uma STRING de texto. É OBRIGATÓRIO manter todos os zeros à esquerda e todos os dígitos. É proibido converter para número inteiro; trate como uma máscara de texto literal (ex: '000.089.123').

Além disso, CLASSIFIQUE a Nota Fiscal em uma categoria conforme
as opções abaixo.
Retorne também um objeto "Classificacao" com as chaves:
- categoria (string)
- termos_detectados (lista de strings com palavras/frases que
embasaram a classificação)

Classificação:
- INSUMOS AGRÍCOLAS: Sementes; Fertilizantes; Defensivos Agrícolas; Corretivos
- MANUTENÇÃO E OPERAÇÃO: Combustíveis e Lubrificantes; Peças, Parafusos; Componentes Mecânicos; Manutenção de Máquinas e Equipamentos; Pneus, Filtros, Correias; Ferramentas e Utensílios
- RECURSOS HUMANOS: Mão de Obra Temporária; Salários e Encargos
- SERVIÇOS OPERACIONAIS: Frete e Transporte; Colheita Terceirizada; Secagem e Armazenagem; Pulverização e Aplicação
- INFRAESTRUTURA E UTILIDADES: Energia Elétrica; Arrendamento de Terras; Construções e Reformas; Materiais de Construção 
- ADMINISTRATIVAS: Honorários (Contábeis, Advocatícios, Agronômicos); Despesas Bancárias e Financeiras
- SEGUROS E PROTEÇÃO: Seguro Agrícola, Seguro de Ativos (Máquinas/Veículos); Seguro Prestamista
- IMPOSTOS E TAXAS: ITR, IPTU, IPVA, INCRA-CCIR
- INVESTIMENTOS: Aquisição de Máquinas e Implementos; Aquisição de Veículos; Aquisição de Imóveis; Infraestrutura Rural

Critérios:
- NÃO desista da classificação. Se os produtos não forem estritamente agrícolas (ex: itens de festa, alimentos), utilize a lógica de uso no ambiente rural.
- Itens de consumo geral, limpeza, alimentação ou eventos/festas devem ser classificados como "ADMINISTRATIVAS" (Despesas Diversas).
- Ferramentas pequenas ou itens de manutenção predial devem ir para "MANUTENÇÃO E OPERAÇÃO".
- SEJA ANALÍTICO: Se encontrar 'Balão' ou 'Bala de coco', o termo detectado é o próprio item, e a categoria é 'ADMINISTRATIVAS' por ser uma despesa de consumo/social da unidade produtora.
- A categoria "Não Classificado" só deve ser usada se o texto for completamente ilegível.

Texto:
{texto}
"""

            response = self.model.generate_content(prompt)
            dados_extraidos = self.processar_resposta_ia(response.text)

            return {
                'success': True,
                'dados_extraidos': dados_extraidos
            }

        except Exception as e:
            erro_str = str(e)
            if "429" in erro_str or "Quota exceeded" in erro_str:
                return {
                    'success': False,
                    'error': 'Limite de requisições da IA atingido. O plano gratuito do Gemini permite poucas requisições por minuto. Por favor, aguarde cerca de 1 minuto e tente novamente!'
                }
            return {
                'success': False,
                'error': f'Erro durante extração: {erro_str}'
            }
