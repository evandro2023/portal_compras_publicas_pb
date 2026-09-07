"""Script de consulta e enriquecimento da localização (UF e Município) dos fornecedores das contratações públicas da Paraíba.

Utiliza a API pública gratuita MinhaReceita / Dados Abertos para consultar os CNPJs únicos das empresas contratadas,
gravando a tabela `dim_fornecedores_uf` no DuckDB (data/compras_pb.duckdb).
"""

from __future__ import annotations

import time
from pathlib import Path
import duckdb
import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "compras_pb.duckdb"
API_URL = "https://minhareceita.org/{cnpj}"


def buscar_dados_cnpj(cnpj: str, max_retries: int = 2) -> dict | None:
    """Consulta os dados da empresa via API pública MinhaReceita."""
    cnpj_clean = str(cnpj).zfill(14)
    url = API_URL.format(cnpj=cnpj_clean)

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "cnpj": cnpj_clean,
                    "razao_social": data.get("razao_social"),
                    "nome_fantasia": data.get("nome_fantasia"),
                    "uf": data.get("uf"),
                    "municipio": data.get("municipio"),
                    "porte": data.get("porte"),
                    "cnae_fiscal": data.get("cnae_fiscal"),
                    "cnae_descricao": data.get("cnae_fiscal_descricao"),
                    "is_paraiba": data.get("uf") == "PB",
                }
            elif response.status_code == 429:
                time.sleep(1.5)
        except Exception:
            pass
        time.sleep(0.3)

    return None


def enriquece_fornecedores_uf(db_path: Path = DB_PATH, limit_cnpjs: int = 300) -> None:
    """Extrai os CNPJs com maior volume financeiro contratado e enriquece a localização no DuckDB."""
    print("=== Iniciando Enriquecimento de Localização dos Fornecedores (UF/Município) ===")
    
    conn = duckdb.connect(str(db_path))
    
    # Busca os CNPJs únicos mais relevantes em volume de compras
    query = """
        SELECT 
            REGEXP_REPLACE(cnpjCpf, '[^0-9]', '', 'g') as cnpj_clean,
            MAX(contratado) as nome_contratado,
            SUM(valorTotal) as total_valor
        FROM contratos
        WHERE cnpjCpf IS NOT NULL AND LENGTH(REGEXP_REPLACE(cnpjCpf, '[^0-9]', '', 'g')) = 14
        GROUP BY cnpj_clean
        ORDER BY total_valor DESC
    """
    if limit_cnpjs > 0:
        query += f" LIMIT {limit_cnpjs}"

    df_cnpjs = conn.execute(query).df()
    print(f"-> Total de CNPJs selecionados para consulta: {len(df_cnpjs)}")

    # Verifica se já existe tabela parcial no DuckDB para não re-consultar
    tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
    existing_cnpjs = set()
    existing_records = []
    
    if "dim_fornecedores_uf" in tables:
        df_exist = conn.execute("SELECT * FROM dim_fornecedores_uf").df()
        existing_cnpjs = set(df_exist["cnpj"].astype(str).str.zfill(14).unique())
        existing_records = df_exist.to_dict(orient="records")
        print(f"  ✓ {len(existing_cnpjs)} CNPJs já enriquecidos anteriormente mantidos.")

    new_records = []
    total_paraiba = 0
    total_outros_estados = 0

    for idx, row in df_cnpjs.iterrows():
        cnpj = str(row["cnpj_clean"]).zfill(14)
        if cnpj in existing_cnpjs:
            continue

        res = buscar_dados_cnpj(cnpj)
        if res:
            new_records.append(res)
            if res["is_paraiba"]:
                total_paraiba += 1
            else:
                total_outros_estados += 1
            print(f" [{idx+1}/{len(df_cnpjs)}] {res['razao_social']} -> UF: {res['uf']} ({res['municipio']})")
        else:
            # Fallback caso a API falhe para um CNPJ específico
            new_records.append({
                "cnpj": cnpj,
                "razao_social": row["nome_contratado"],
                "nome_fantasia": row["nome_contratado"],
                "uf": "N/D",
                "municipio": "N/D",
                "porte": "N/D",
                "cnae_fiscal": None,
                "cnae_descricao": None,
                "is_paraiba": False,
            })
        time.sleep(0.15) # Pequena pausa respeitosa entre requisições

    all_records = existing_records + new_records
    if all_records:
        df_final = pd.DataFrame(all_records)
        conn.execute("CREATE OR REPLACE TABLE dim_fornecedores_uf AS SELECT * FROM df_final")
        print(f"\n✓ Tabela 'dim_fornecedores_uf' salva no DuckDB com {len(df_final)} fornecedores.")

        # Salva em CSV na pasta data/processed para auditabilidade e exportação
        csv_out = PROJECT_ROOT / "data" / "processed" / "dim_fornecedores_uf.csv"
        csv_out.parent.mkdir(parents=True, exist_ok=True)
        df_final.to_csv(csv_out, index=False, encoding="utf-8")
        print(f"✓ Arquivo CSV exportado com sucesso: {csv_out}")

    conn.close()



if __name__ == "__main__":
    enriquece_fornecedores_uf(limit_cnpjs=250)
