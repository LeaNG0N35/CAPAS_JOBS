from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
import pandas as pd
from pathlib import Path
from datetime import datetime

TEMPLATE_DIR = Path(__file__).parent / "templates"

@dataclass
class Job:
    jobname: str
    workflow_name: str = ""
    application: str = ""
    group: str = ""
    parameters: str = ""
    predecessors: List[str] = None
    successors: List[str] = None
    log_path: str = ""
    input_path: str = ""
    output_path: str = ""
    naming: str = ""
    process_description: str = ""
    functionality_description: str = ""

    @property
    def parameters_list(self) -> List[str]:
        if not self.parameters:
            return []
        # Quebra por linha; limpa espaços; ignora linhas vazias
        return [line.strip() for line in self.parameters.splitlines() if line.strip()]

def normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    # vírgulas para separar múltiplos
    return [x.strip() for x in str(value).split(",") if x.strip()]

def jobs_from_dataframe(df: pd.DataFrame) -> List[Job]:
    # normaliza colunas (case-insensitive)
    cols = {c.lower(): c for c in df.columns}
    def get(row, key):
        src = cols.get(key, None)
        return row[src] if src in row else ""

    jobs: List[Job] = []
    for _, row in df.iterrows():
        job = Job(
            jobname=str(get(row, "jobname")).strip(),
            workflow_name=str(get(row, "workflow_name")).strip(),
            application=str(get(row, "application")).strip(),
            group=str(get(row, "group")).strip(),
            parameters=str(get(row, "parameters")).strip(),
            predecessors=normalize_list(get(row, "predecessors")),
            successors=normalize_list(get(row, "successors")),
            log_path=str(get(row, "log_path")).strip(),
            input_path=str(get(row, "input_path")).strip(),
            output_path=str(get(row, "output_path")).strip(),
            naming=str(get(row, "naming")).strip(),
            process_description=str(get(row, "process_description")).strip(),
            functionality_description=str(get(row, "functionality_description")).strip(),
        )
        if not job.jobname:
            continue
        jobs.append(job)
    return jobs

def render_job_covers(jobs: List[Job], out_dir: Path) -> None:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(disabled_extensions=("txt",))
    )
    template = env.get_template("job_cover.txt.j2")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for job in jobs:
        text = template.render(job=job, generated_at=ts)
        (out_dir / f"{job.jobname}.txt").write_text(text, encoding="utf-8")

def build_summary_excel(jobs: List[Job], path: Path) -> None:
    rows = []
    for j in jobs:
        d = asdict(j)
        d["predecessors"] = ", ".join(j.predecessors or [])
        d["successors"] = ", ".join(j.successors or [])
        d["parameters_list"] = "\n".join(j.parameters_list)
        rows.append(d)
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="jobs")

if __name__ == "__main__":
    # Exemplo rápido (manual)
    sample = Job(
        jobname="JOB_EXEMPLO",
        workflow_name="WF_EXEMPLO",
        application="APLICACAO_X",
        group="GRUPO_A",
        parameters="DATA=20250101\nAMBIENTE=HML",
        predecessors=["JOB_INICIAL_A", "JOB_INICIAL_B"],
        successors=["JOB_FINAL"],
        log_path="/logs/job_exemplo.log",
        input_path="/data/in",
        output_path="/data/out",
        naming="BI_JOB_EXEMPLO_YYYYMMDD",
        process_description="Processa dados de exemplo",
        functionality_description="Gera outputs de teste"
    )
    out = Path("out")
    render_job_covers([sample], out)
    build_summary_excel([sample], out / "jobs_summary.xlsx")
    print("Arquivos gerados em", out)
