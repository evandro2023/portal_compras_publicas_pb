"""Script de ingestão e atualização dos dados do CAGED (Paraíba) e tabelas auxiliares para o DuckDB.

Permite ingestão completa ou incremental (apenas meses ainda não salvos), salvando os arquivos anuais
em formato CSV e Parquet, e atualizando o banco DuckDB (data/compras_pb.duckdb).

Uso:
  python src/caged/ingest_caged.py [--incremental] [--anos 2025 2026] [--niveis secao classe subclasse]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import duckdb
import pandas as pd

from src.caged.data import PROCESSED_DIR, PROJECT_ROOT, baixar_caged_municipios_pb

DB_PATH = PROJECT_ROOT / "data" / "compras_pb.duckdb"
CAGED_DIR = PROCESSED_DIR / "caged"
SECAO_CLASSE_CSV = PROJECT_ROOT / "src" / "caged" / "secao_classe.csv"


def baixar_dados_caged(
    anos: list[int] = [2025, 2026],
    niveis: list[str] = ["secao", "classe", "subclasse"],
    output_dir: Path = CAGED_DIR,
    incremental: bool = False,
) -> list[Path]:
    """Baixa e consolida os dados do CAGED para os anos e níveis especificados.
    
    Salva os arquivos no formato `caged_pb_<nivel>_<ano>.csv` e `caged_pb_<nivel>_<ano>.parquet`.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []

    modo_str = "incremental" if incremental else "completo"
    print(f"=== Iniciando Ingestão CAGED PB (Modo: {modo_str}) ===")

    for ano in anos:
        for nivel in niveis:
            print(f"-> Processando CAGED PB ({ano}) - Nível: {nivel}...")
            try:
                baixar_caged_municipios_pb(
                    ano=ano,
                    nivel=nivel,
                    output_dir=output_dir,
                    salvar_csv=True,
                    salvar_parquet=True,
                    continuar_ao_falhar=True,
                    incremental=incremental,
                )
                csv_path = output_dir / f"caged_pb_{nivel}_{ano}.csv"
                parquet_path = output_dir / f"caged_pb_{nivel}_{ano}.parquet"
                if csv_path.exists():
                    generated_files.append(csv_path)
                if parquet_path.exists():
                    generated_files.append(parquet_path)
                print(f"   [OK] {csv_path.name} e {parquet_path.name}")
            except Exception as exc:
                print(f"   [ERRO] Falha ao processar CAGED PB {ano} nível {nivel}: {exc}")

    return generated_files


def carregar_caged_duckdb(db_path: str | Path = DB_PATH, caged_dir: str | Path = CAGED_DIR) -> None:
    """Carrega os arquivos parquet do CAGED e o arquivo secao_classe.csv no DuckDB."""
    db_path = Path(db_path)
    caged_dir = Path(caged_dir)

    conn = duckdb.connect(str(db_path))

    # 1. Carregar tabela secao_classe
    if SECAO_CLASSE_CSV.exists():
        print(f"Carregando {SECAO_CLASSE_CSV.name} no DuckDB...")
        df_secao_classe = pd.read_csv(SECAO_CLASSE_CSV, sep=";", dtype=str)
        # Normalizar nomes de colunas sem espaços/acentos
        df_secao_classe.columns = [c.strip().lower().replace("çã", "ca").replace("é", "e") for c in df_secao_classe.columns]
        conn.execute("CREATE OR REPLACE TABLE caged_secao_classe AS SELECT * FROM df_secao_classe")
        print(f"  ✓ Tabela 'caged_secao_classe' criada com {len(df_secao_classe)} registros.")
    else:
        print(f"  [AVISO] Arquivo {SECAO_CLASSE_CSV} não encontrado.")

    # 2. Carregar tabelas anuais/consolidadas por nível do CAGED
    parquet_files = list(caged_dir.glob("caged_pb_*.parquet"))
    if not parquet_files:
        print(f"  [AVISO] Nenhum arquivo parquet do CAGED encontrado em {caged_dir}")
    else:
        for pfile in parquet_files:
            table_name = pfile.stem  # ex: caged_pb_secao_2025
            print(f"Carregando {pfile.name} na tabela '{table_name}'...")
            conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{pfile}')")
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"  ✓ Tabela '{table_name}' criada com {count} registros.")

    print("\n--- Tabelas no DuckDB ---")
    tables = conn.execute("SHOW TABLES").fetchall()
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
        print(f"- {t[0]}: {count} linhas")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Ingestão de dados do CAGED PB para o DuckDB")
    parser.add_argument("--incremental", action="store_true", help="Baixa apenas os meses ainda não processados no ano")
    parser.add_argument("--anos", nargs="+", type=int, default=[2025, 2026], help="Anos a serem processados")
    parser.add_argument("--niveis", nargs="+", type=str, default=["secao", "classe", "subclasse"], help="Níveis CNAE a serem processados")

    args = parser.parse_args()

    baixar_dados_caged(anos=args.anos, niveis=args.niveis, incremental=args.incremental)
    carregar_caged_duckdb()
    print("=== Processo concluído com sucesso! ===")


if __name__ == "__main__":
    main()
