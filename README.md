# CashFlow - Sistema de Gestão Financeira com IA Administrativa 🚀

Este projeto consiste em uma plataforma inteligente para controle de movimentações financeiras corporativas (A Pagar e A Receber), desenvolvido como parte dos requisitos práticos de Engenharia de Software.

O sistema conta com regras rígidas de consistência de parcelamentos, auditoria automatizada e um pipeline de **Inteligência Artificial Híbrida via RAG** (Retrieval-Augmented Generation) integrado à API do Google Gemini.

---

## 🛠️ Tecnologias Utilizadas

* **Back-end:** Django 5.0 + Django REST Framework (DRF)
* **Banco de Dados:** SQLite (padrão nesta versão de deploy/produção) / PostgreSQL (disponível via Docker)
* **Arquitetura de Dados:** NumPy (Processamento e similaridade vetorial matemática para RAG com embeddings)
* **Inteligência Artificial:** SDK Google GenAI (`gemini-2.5-flash`, `gemini-2.5-flash-lite` e `gemini-embedding-001` / `text-embedding-004`)
* **Front-end:** HTML5, CSS3, Bootstrap 5 e JavaScript Assíncrono (Fetch API)
* **Extração de Dados:** PyPDF2 (Leitura de texto de PDFs de Notas Fiscais)
* **Infraestrutura:** Docker e Docker Compose (para ambiente PostgreSQL)

---

## 📂 Estrutura de Repositórios

Para cumprir todas as exigências (entrega de ambiente conteinerizado e hospedagem em servidor público), o projeto foi estruturado em dois ambientes:

1. **Repositório Principal (Docker & PostgreSQL):**
   * Link: [https://github.com/yago-lc02/projeto-administrativo](https://github.com/yago-lc02/projeto-administrativo)
   * Configurado para rodar a aplicação integrada ao PostgreSQL via containers Docker.
2. **Repositório de Deploy (Produção SQLite - Este Repositório):**
   * Link: [https://github.com/guiLhermeDev1050/projeto-administrativo-sqlite](https://github.com/guiLhermeDev1050/projeto-administrativo-sqlite)
   * Adaptado para rodar sob o motor SQLite para viabilizar a hospedagem gratuita na nuvem do PythonAnywhere (onde contêineres e bancos externos não são suportados).
   * **URL de Produção:** [https://cashflowapp.pythonanywhere.com/financeiro/lancamentos/](https://cashflowapp.pythonanywhere.com/financeiro/lancamentos/)

---

## ⚙️ Funcionalidades Principais

1. **Painel de Lançamentos:** Listagem reativa de contas a pagar e a receber com filtros simultâneos por descrição, tipo e parceiro.
2. **Módulo de Parceiros (Pessoas):** CRUD completo para gerenciar Fornecedores, Clientes e Faturados, incluindo controle de status ativo/inativo e regras de reativação lógica.
3. **Módulo de Categorias (Classificações):** Interface para controle de classificações financeiras associadas a receitas ou despesas.
4. **Geração Consistente de Parcelas:** Divisão automática de valores com paridade de consistência e vencimentos de 30 em 30 dias.
5. **Alteração Segura:** Recálculo automático das parcelas quando o valor de um lançamento principal é alterado.
6. **Exclusão Lógica Unificada:** Inativação de registros (`status_ativo=False`) em cascata para manter a integridade dos dados históricos.
7. **Interpretador de PDFs (Upload):** Extração inteligente de dados de Notas Fiscais diretamente em formato JSON via IA, com validação de máscara de CNPJ/CPF e números de nota fiscal.
8. **Analisador de JSON:** Interface para validar se os dados extraídos de um PDF já existem no banco ou precisam ser cadastrados.
9. **Auditor Sênior (Chat RAG):** Chat integrado alimentado por IA capaz de responder a perguntas sobre o banco usando duas abordagens:
   * **RAG Simples:** Envia os metadados textuais mais recentes do banco como contexto para o modelo.
   * **RAG Embeddings:** Realiza busca semântica calculando a similaridade por cosseno entre o vetor da pergunta e o vetor de cada movimentação (utilizando NumPy) para selecionar os contextos mais relevantes.

---

## ⚙️ Instalação e Execução Local

### Opção A: Execução Local Rápida (SQLite)

Esta opção não necessita do Docker e é a maneira mais simples de testar o sistema localmente.

1. **Clonar o Repositório:**
   ```bash
   git clone https://github.com/guiLhermeDev1050/projeto-administrativo-sqlite.git
   cd projeto-administrativo-sqlite
   ```

2. **Criar e Ativar Ambiente Virtual:**
   * No Windows:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * No Linux/macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instalar Dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Variáveis de Ambiente:**
   Crie um arquivo `.env` na raiz do projeto e configure a sua chave da API do Google Gemini:
   ```env
   GEMINI_API_KEY=sua_chave_aqui
   ```

5. **Aplicar Migrações do Banco de Dados:**
   ```bash
   python manage.py migrate
   ```

6. **Carregar Carga de Dados Seed (Opcional):**
   Para testar o RAG com um banco já estruturado, execute o comando personalizado que limpa a base e injeta 200 movimentações realistas e comutadas:
   ```bash
   python manage.py carregar_dados
   ```

7. **Criar Superusuário (Para acessar o Django Admin):**
   ```bash
   python manage.py createsuperuser
   ```

8. **Executar o Servidor:**
   ```bash
   python manage.py runserver
   ```
   Acesse no navegador: [http://127.0.0.1:8000/financeiro/lancamentos/](http://127.0.0.1:8000/financeiro/lancamentos/)

---

### Opção B: Execução via Docker (PostgreSQL)

Caso queira subir o ambiente conteinerizado completo com PostgreSQL:

1. **Preparar as Variáveis:**
   Garanta que o arquivo `.env` contenha a chave do Gemini e as variáveis correspondentes:
   ```env
   GEMINI_API_KEY=sua_chave_aqui
   ```

2. **Subir os Containers:**
   Na raiz do projeto, execute:
   ```bash
   docker-compose up --build
   ```

3. **Rodar Migrações e Seeds no Container:**
   Abra outro terminal e execute:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py carregar_dados
   ```

4. **Acessar a Aplicação:**
   O container expõe a porta `8001` no host:
   [http://127.0.0.1:8001/financeiro/lancamentos/](http://127.0.0.1:8001/financeiro/lancamentos/)

---

## 🔑 Credenciais e Acesso (Produção/Hospedagem)

* **URL de Produção:** [https://cashflowapp.pythonanywhere.com/financeiro/lancamentos/](https://cashflowapp.pythonanywhere.com/financeiro/lancamentos/)
* **Painel Administrativo:** [https://cashflowapp.pythonanywhere.com/admin/login/](https://cashflowapp.pythonanywhere.com/admin/login/)
* **Usuário Admin:** `administrador`
* **Senha Admin:** `administrador`

---

## 🗺️ Principais Rotas e Endpoints

* **Listagem e Gestão Financeira:** `/financeiro/lancamentos/`
* **Inclusão de Lançamento:** `/financeiro/lancamentos/incluir/`
* **CRUD de Parceiros (Pessoas):** `/financeiro/pessoas/`
* **CRUD de Categorias (Classificações):** `/financeiro/classificacoes/`
* **Auditor RAG (Chat Inteligente):** `/financeiro/chat/`
* **Upload e Extração de PDFs:** `/interpreter/`
* **Verificação e Importação de JSON:** `/financeiro/analisador/`
