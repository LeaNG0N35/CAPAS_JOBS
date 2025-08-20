import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
from generator import Job, render_job_covers, build_summary_excel, jobs_from_dataframe

st.set_page_config(page_title="Gerador de Capas de Jobs", layout="wide")

import os
APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()
if APP_PASSWORD:
    pw = st.sidebar.text_input("Senha de acesso", type="password", value="")
    if pw != APP_PASSWORD:
        st.title("🗂️ Gerador de Capas de Jobs (.txt) + Excel")
        st.warning("Aplicação protegida. Informe a senha correta na barra lateral para acessar.")
        st.stop()


st.title("🗂️ Gerador de Capas de Jobs (.txt) + Excel")
st.write("Preencha o formulário para um job único **ou** faça upload da planilha para gerar em lote.")

with st.expander("📥 Download do modelo de planilha (example_input.xlsx)"):
    tmpl = pd.DataFrame([{
        "jobname":"JOB_EXEMPLO",
        "workflow_name":"WF_EXEMPLO",
        "application":"APLICACAO_X",
        "group":"GRUPO_A",
        "parameters":"DATA=20250101\nAMBIENTE=HML",
        "predecessors":"JOB_A, JOB_B",
        "successors":"JOB_C",
        "log_path":"/logs/JOB_EXEMPLO.log",
        "input_path":"/data/in",
        "output_path":"/data/out",
        "naming":"BI_JOB_EXEMPLO_YYYYMMDD",
        "process_description":"Processa dados de exemplo",
        "functionality_description":"Gera outputs de teste"
    }])
    st.dataframe(tmpl)
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        tmpl.to_excel(writer, index=False, sheet_name="jobs")
    st.download_button("Baixar modelo (.xlsx)", bio.getvalue(), "example_input.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.header("➊ Job único (formulário)")
with st.form("single_job"):
    c1, c2, c3 = st.columns(3)
    jobname = c1.text_input("jobname *", value="JOB_EXEMPLO")
    workflow_name = c2.text_input("workflow_name")
    application = c3.text_input("application")
    group = c1.text_input("group")
    predecessors = c2.text_input("predecessors (separe por vírgula)")
    successors = c3.text_input("successors (separe por vírgula)")
    log_path = c1.text_input("log_path", value="/logs/JOB_EXEMPLO.log")
    input_path = c2.text_input("input_path", value="/data/in")
    output_path = c3.text_input("output_path", value="/data/out")
    naming = c1.text_input("naming", value="BI_JOB_EXEMPLO_YYYYMMDD")
    parameters = st.text_area("parameters (uma por linha: CHAVE=VALOR)", value="DATA=20250101\nAMBIENTE=HML")
    process_description = st.text_area("process_description", value="Processa dados de exemplo")
    functionality_description = st.text_area("functionality_description", value="Gera outputs de teste")
    submitted = st.form_submit_button("➕ Adicionar à lista")

if "jobs_buffer" not in st.session_state:
    st.session_state.jobs_buffer = []

if submitted:
    if not jobname.strip():
        st.error("O campo jobname é obrigatório.")
    else:
        st.session_state.jobs_buffer.append({
            "jobname": jobname.strip(),
            "workflow_name": workflow_name.strip(),
            "application": application.strip(),
            "group": group.strip(),
            "parameters": parameters,
            "predecessors": predecessors,
            "successors": successors,
            "log_path": log_path.strip(),
            "input_path": input_path.strip(),
            "output_path": output_path.strip(),
            "naming": naming.strip(),
            "process_description": process_description.strip(),
            "functionality_description": functionality_description.strip()
        })
        st.success(f"Job '{jobname}' adicionado à lista.")

st.header("➋ Lote via planilha (.xlsx)")
uploaded = st.file_uploader("Envie a planilha (aba 'jobs'). Colunas: ver modelo acima.", type=["xlsx"])
batch_df = None
if uploaded is not None:
    try:
        batch_df = pd.read_excel(uploaded, sheet_name="jobs")
        st.write("Prévia dos dados lidos:")
        st.dataframe(batch_df.head(20))
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")

st.header("➌ Gerar arquivos")
generate = st.button("🚀 Gerar capas (.txt) + Excel")
if generate:
    jobs = []
    # buffer do formulário
    if st.session_state.jobs_buffer:
        jobs.extend(jobs_from_dataframe(pd.DataFrame(st.session_state.jobs_buffer)))
    # planilha
    if batch_df is not None:
        jobs.extend(jobs_from_dataframe(batch_df))

    # dedup por jobname preservando ordem
    seen = set()
    unique_jobs = []
    for j in jobs:
        if j.jobname not in seen:
            seen.add(j.jobname)
            unique_jobs.append(j)
    jobs = unique_jobs

    if not jobs:
        st.error("Nenhum job para gerar. Adicione pelo menos um via formulário ou planilha.")
    else:
        # renderizar para memória e montar um zip
        out_mem = BytesIO()
        from zipfile import ZipFile, ZIP_DEFLATED
        from datetime import datetime

        with ZipFile(out_mem, "w", ZIP_DEFLATED) as z:
            # capas
            from jinja2 import Environment, FileSystemLoader, select_autoescape
            env = Environment(
                loader=FileSystemLoader("templates"),
                autoescape=select_autoescape(disabled_extensions=("txt",))
            )
            template = env.get_template("job_cover.txt.j2")
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows = []
            for job in jobs:
                text = template.render(job=job, generated_at=ts)
                z.writestr(f"capas/{job.jobname}.txt", text)
                rows.append({
                    "jobname": job.jobname,
                    "workflow_name": job.workflow_name,
                    "application": job.application,
                    "group": job.group,
                    "parameters": "\n".join(job.parameters_list),
                    "predecessors": ", ".join(job.predecessors or []),
                    "successors": ", ".join(job.successors or []),
                    "log_path": job.log_path,
                    "input_path": job.input_path,
                    "output_path": job.output_path,
                    "naming": job.naming,
                    "process_description": job.process_description,
                    "functionality_description": job.functionality_description,
                })
            # excel resumo
            df = pd.DataFrame(rows)
            from io import BytesIO
            bio = BytesIO()
            with pd.ExcelWriter(bio, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="jobs")
            z.writestr("jobs_summary.xlsx", bio.getvalue())

        st.download_button("📦 Baixar ZIP com capas + Excel", out_mem.getvalue(), "jobs_output.zip", mime="application/zip")
        st.success(f"Foram gerados {len(jobs)} jobs.")
