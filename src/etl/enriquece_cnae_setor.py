"""Script de enriquecimento e classificação dos fornecedores por CNAE, Setor Econômico,
Intensidade Tecnológica e Localização Geográfica no DuckDB.
"""

from __future__ import annotations
from pathlib import Path
import duckdb
import pandas as pd

from src.etl.cnae_catalog import (
    categorizar_intensidade_tecnologica,
    categorizar_localizacao,
    categorizar_setor_cnae,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "compras_pb.duckdb"


def executar_enriquecimento_cnae_setor(db_path: Path = DB_PATH) -> None:
    """Processa a tabela dim_fornecedores_uf, aplica as taxonomias e cria a view analítica."""
    print("=== Iniciando Enriquecimento por CNAE, Setor e Intensidade Tecnológica ===")
    conn = duckdb.connect(str(db_path))

    tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
    if "dim_fornecedores_uf" not in tables:
        print("⚠️ Tabela dim_fornecedores_uf não encontrada no DuckDB.")
        return

    df_fornecedores = conn.execute("SELECT * FROM dim_fornecedores_uf").df()
    print(f"-> Fornecedores encontrados em dim_fornecedores_uf: {len(df_fornecedores)}")

    # Aplicação das classificações
    df_fornecedores["localizacao_categoria"] = df_fornecedores.apply(
        lambda r: categorizar_localizacao(r.get("uf"), r.get("municipio")), axis=1
    )

    df_fornecedores["setor_economico"] = df_fornecedores["cnae_fiscal"].apply(
        categorizar_setor_cnae
    )

    df_fornecedores["intensidade_tecnologica"] = df_fornecedores["cnae_fiscal"].apply(
        categorizar_intensidade_tecnologica
    )

    # Gravação no DuckDB
    conn.register("df_dim_cnae_temp", df_fornecedores)
    conn.execute("""
        CREATE OR REPLACE TABLE dim_fornecedores_cnae AS
        SELECT * FROM df_dim_cnae_temp
    """)
    print("  ✓ Tabela `dim_fornecedores_cnae` atualizada com sucesso.")

    # Criação da view unificada com os contratos
    conn.execute("""
        CREATE OR REPLACE VIEW vw_analise_compras_cnae_localizacao AS
        SELECT 
            c.registroCge,
            c.numeroContrato,
            c.nomeOrgao,
            c.dataAssinatura,
            COALESCE(c.ano_referencia, YEAR(TRY_CAST(c.dataAssinatura AS DATE))) as ano_contrato,
            c.valorTotal,
            c.contratado as nome_contratado_contrato,
            REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') as cnpj_clean,
            f.razao_social,
            f.uf,
            f.municipio as municipio_fornecedor,
            COALESCE(f.localizacao_categoria, 'Não Identificado') as localizacao_categoria,
            COALESCE(f.cnae_fiscal, 0) as cnae_fiscal,
            COALESCE(f.cnae_descricao, 'Não Informado') as cnae_descricao,
            COALESCE(f.setor_economico, 'Não Classificado') as setor_economico,
            COALESCE(f.intensidade_tecnologica, 'Não Classificado') as intensidade_tecnologica
        FROM contratos c
        LEFT JOIN dim_fornecedores_cnae f 
            ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = LPAD(CAST(CAST(f.cnpj AS BIGINT) AS VARCHAR), 14, '0')
    """)
    print("  ✓ View `vw_analise_compras_cnae_localizacao` criada com sucesso.")

    # Resumo
    df_resumo_loc = conn.execute("""
        SELECT localizacao_categoria, COUNT(*) as total_contratos, SUM(valorTotal) as total_valor
        FROM vw_analise_compras_cnae_localizacao
        GROUP BY localizacao_categoria
        ORDER BY total_valor DESC
    """).df()

    print("\n--- Resumo por Localização ---")
    print(df_resumo_loc.to_string(index=False))

    df_resumo_setor = conn.execute("""
        SELECT setor_economico, COUNT(*) as total_contratos, SUM(valorTotal) as total_valor
        FROM vw_analise_compras_cnae_localizacao
        GROUP BY setor_economico
        ORDER BY total_valor DESC
    """).df()

    print("\n--- Resumo por Setor Econômico ---")
    print(df_resumo_setor.to_string(index=False))

    conn.close()
    print("\n=== Processamento Concluído ===")


if __name__ == "__main__":
    executar_enriquecimento_cnae_setor()
