# Job Cover Automation (CTRL-M / Jobs)

Uma automação simples para gerar **capas de jobs (.txt)** e um **relatório Excel** a partir de um formulário ou planilha.
Pensado para uso local via **Streamlit** para você e seu time.

## Como rodar (local)
1) Crie e ative um ambiente virtual (opcional, mas recomendado)
```
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```
2) Instale dependências
```
pip install -r requirements.txt
```
3) Execute a aplicação web local
```
streamlit run app_streamlit.py
```
4) No navegador, preencha o formulário (job único) **ou** faça upload da planilha `example_input.xlsx` (lote).
5) Faça o download do **ZIP** com as capas `.txt` e do **.xlsx** de resumo.

## Estrutura dos dados (campos)
- `jobname` (obrigatório)
- `workflow_name`
- `application`
- `group`
- `parameters` (texto livre; pode usar chave=valor separados por quebra de linha)
- `predecessors` (separe múltiplos por vírgula)
- `successors` (separe múltiplos por vírgula)
- `log_path`
- `input_path`
- `output_path`
- `naming`
- `process_description`
- `functionality_description`

## Saídas
- Uma capa `.txt` por job usando `templates/job_cover.txt.j2` (customizável).
- Um Excel `jobs_summary.xlsx` com todos os campos.
- Um ZIP contendo tudo.

## Customização
- Edite o arquivo `templates/job_cover.txt.j2` para mudar o layout das capas.
- Ajuste `generator.py` se quiser regras de negócio extras (validações, normalização, etc.).

## Deploy para compartilhar via link

### Opção A) Streamlit Community Cloud (mais simples)
1) Suba esta pasta para um repositório **GitHub** (público ou privado).
2) Acesse **share.streamlit.io** e conecte seu GitHub.
3) Selecione o repositório e o arquivo `app_streamlit.py` como entrypoint.
4) (Opcional) Em **Secrets**, adicione `APP_PASSWORD` para proteger o acesso com senha.
5) A plataforma gera um **link** que você pode enviar para seu time.

### Opção B) Render.com (Docker)
1) Faça login no **Render** e conecte seu GitHub.
2) Clique em *New +* → *Blueprint* e aponte para o repo com este projeto.
3) O arquivo `render.yaml` já está pronto. Render vai buildar a imagem Docker.
4) Defina a variável de ambiente `APP_PASSWORD` (opcional) para proteger o app.
5) Ao terminar o deploy, Render fornece um **link público**.

### Opção C) Docker (qualquer servidor)
```
docker build -t job-covers .
docker run -p 8501:8501 -e APP_PASSWORD="sua_senha" job-covers
```
Acesse http://SEU_SERVIDOR:8501 e compartilhe a URL com o time.

> **Dica:** Se precisar de autenticação corporativa (SSO/AD/OAuth), dá pra colocar um *reverse proxy* (Nginx/Traefik) na frente com autenticação, ou migrar para um backend FastAPI com login e deixar o Streamlit só como frontend.
