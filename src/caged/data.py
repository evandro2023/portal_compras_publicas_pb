"""Funcoes de apoio para baixar, ler e preparar dados do Novo CAGED."""

from __future__ import annotations

import os
import tempfile
import warnings
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd
import pycaged

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

PB_UF_CODE = 25
NOVO_CAGED_URL_TEMPLATE = (
    "ftp://ftp.mtps.gov.br/pdet/microdados/NOVO CAGED/"
    "{year}/{competence}/CAGEDMOV{competence}.7z"
)

DEFAULT_COLUMNS = [
    "competênciamov",
    "uf",
    "município",
    "seção",
    "subclasse",
    "saldomovimentação",
    "cbo2002ocupação",
    "categoria",
    "graudeinstrução",
    "idade",
    "raçacor",
    "sexo",
    "salário",
    "tipomovimentação",
]

PYCAGED_LEVELS = {
    "secao": pycaged.SecaoMunicipios,
    "classe": pycaged.ClasseMunicipios,
    "subclasse": pycaged.SubclasseMunicipios,
}


def download_file(url: str, destination: str | Path, overwrite: bool = False) -> Path:
    """Baixa um arquivo para `destination` quando ele ainda nao existe."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not overwrite:
        return destination

    urlretrieve(url, destination)
    return destination


def build_caged_url(year: int, month: int) -> str:
    """Monta a URL FTP oficial do arquivo mensal CAGEDMOV."""
    competence = f"{year}{month:02d}"
    return NOVO_CAGED_URL_TEMPLATE.format(year=year, competence=competence)


def download_month(year: int, month: int, overwrite: bool = False) -> Path:
    """Baixa o arquivo compactado de uma competencia do Novo CAGED."""
    competence = f"{year}{month:02d}"
    destination = RAW_DIR / f"caged_mov_{competence}.7z"
    return download_file(build_caged_url(year, month), destination, overwrite=overwrite)


def extract_caged_txt(archive_path: str | Path, overwrite: bool = False) -> Path:
    """Extrai o TXT CAGEDMOV de um arquivo `.7z` para `data/raw/`."""
    import py7zr

    archive_path = Path(archive_path)
    txt_name = archive_path.stem.upper().replace("CAGED_PB_", "CAGEDMOV")
    if not txt_name.startswith("CAGEDMOV"):
        txt_name = archive_path.stem.replace("caged_mov_", "CAGEDMOV")
    destination = RAW_DIR / f"{txt_name}.txt"

    if destination.exists() and not overwrite:
        return destination

    with py7zr.SevenZipFile(archive_path, mode="r") as archive:
        txt_files = [name for name in archive.getnames() if name.upper().endswith(".TXT")]
        if not txt_files:
            raise FileNotFoundError(f"Nenhum TXT encontrado em {archive_path}")
        archive.extract(path=RAW_DIR, targets=[txt_files[0]])

    extracted = RAW_DIR / txt_files[0]
    if extracted != destination:
        extracted.replace(destination)
    return destination


def load_caged_mov(path: str | Path, columns: list[str] | None = None) -> pd.DataFrame:
    """Le o arquivo TXT do Novo CAGED com separador `;` e decimal brasileiro."""
    path = Path(path)
    usecols = columns or DEFAULT_COLUMNS
    return pd.read_csv(
        path,
        sep=";",
        decimal=",",
        usecols=usecols,
        low_memory=False,
    )


def load_paraiba_mov(path: str | Path, columns: list[str] | None = None) -> pd.DataFrame:
    """Carrega movimentacoes do CAGED e filtra apenas registros da Paraiba."""
    df = load_caged_mov(path, columns=columns)
    return df.loc[df["uf"].eq(PB_UF_CODE)].copy()


def save_paraiba_parquet(
    source_path: str | Path,
    destination_path: str | Path,
    columns: list[str] | None = None,
) -> Path:
    """Gera um Parquet filtrado para Paraiba a partir do TXT original."""
    destination_path = Path(destination_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_paraiba_mov(source_path, columns=columns)
    df.to_parquet(destination_path, index=False)
    return destination_path


def baixar_caged_municipios_pb(
    ano: int,
    nivel: str = "secao",
    output_dir: str | Path = PROCESSED_DIR,
    salvar_csv: bool = True,
    salvar_parquet: bool = True,
    continuar_ao_falhar: bool = True,
    incremental: bool = False,
) -> pd.DataFrame:
    """Baixa meses do CAGED municipal da Paraiba via pycaged.

    Parametros
    ----------
    ano:
        Ano de referencia.
    nivel:
        Nivel CNAE aceito pelo pycaged: `secao`, `classe` ou `subclasse`.
    output_dir:
        Pasta onde os arquivos anuais serao salvos.
    salvar_csv:
        Quando verdadeiro, salva `caged_pb_<nivel>_<ano>.csv`.
    salvar_parquet:
        Quando verdadeiro, salva `caged_pb_<nivel>_<ano>.parquet`.
    continuar_ao_falhar:
        Quando verdadeiro, ignora meses indisponiveis e registra quais falharam.
    incremental:
        Quando verdadeiro, reutiliza o Parquet existente e baixa apenas meses ainda nao salvos.
    """
    if nivel not in PYCAGED_LEVELS:
        valid_levels = ", ".join(PYCAGED_LEVELS)
        raise ValueError(f"Nivel invalido: {nivel}. Use um destes: {valid_levels}.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = output_dir / f"caged_pb_{nivel}_{ano}.parquet"
    existing_df = None
    processed_months = set()

    if incremental and parquet_path.exists():
        try:
            existing_df = pd.read_parquet(parquet_path)
            if "mes" in existing_df.columns:
                processed_months = set(existing_df["mes"].astype(str).str.zfill(2).unique())
        except Exception:
            existing_df = None

    get_month_data = PYCAGED_LEVELS[nivel]
    frames = [existing_df] if existing_df is not None else []
    failed_months = []

    for month in range(1, 13):
        month_text = f"{month:02d}"
        if month_text in processed_months:
            continue

        previous_cwd = Path.cwd()
        try:
            with tempfile.TemporaryDirectory(prefix=f"pycaged_{ano}_{month_text}_") as tmpdir:
                os.chdir(tmpdir)
                with pd.option_context("mode.copy_on_write", False):
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore",
                            category=pd.errors.ChainedAssignmentError,
                        )
                        data = get_month_data(ano, month_text, PB_UF_CODE)
        except Exception as exc:
            if continuar_ao_falhar:
                failed_months.append({"ano": ano, "mes": month_text, "erro": str(exc)})
                continue
            raise
        finally:
            os.chdir(previous_cwd)

        data = data.copy()
        data["ano"] = ano
        data["mes"] = month_text
        frames.append(data)

    if not frames:
        if existing_df is not None:
            return existing_df
        raise RuntimeError(f"Nenhum mes de {ano} foi baixado com sucesso.")

    caged_pb = pd.concat(frames, ignore_index=True)
    if {"Admitidos/Desligados", "Count"}.issubset(caged_pb.columns):
        caged_pb["saldo"] = caged_pb["Admitidos/Desligados"] * caged_pb["Count"]
    caged_pb.attrs["meses_indisponiveis"] = failed_months

    if salvar_csv:
        csv_path = output_dir / f"caged_pb_{nivel}_{ano}.csv"
        caged_pb.to_csv(csv_path, index=False, encoding="utf-8")

    if salvar_parquet:
        caged_pb.to_parquet(parquet_path, index=False)

    return caged_pb

