"""Deduplicação da tabela `contratos` (um registro por contrato).

Problemas observados na carga bruta (data/raw/compras_pb/contratos.csv):
- A mesma extração foi carregada várias vezes (snapshots repetidos).
- Em alguns contratos, snapshots posteriores trazem aditivos/apostilas que
  elevam `valorTotal` (valorTotal = valorOriginal + valorAditivos + valorApostilas).
- Contratos oriundos do PNCP não possuem `registroCge` (NULL); a chave natural
  deles é `urlContrato`. Deduplicar apenas por registroCge colapsaria todos
  esses contratos em um só.

Regra: chave = COALESCE(registroCge, urlContrato). Entre as cópias, mantém-se
a mais completa e atualizada: com CNPJ preenchido, maior valorTotal (aditivos
só acrescem) e maior detalhamento de aditivos.

Aditivos NÃO são linhas separadas: já estão consolidados em `valorTotal`.
`valorOriginal` e a coluna JSON `aditivo` permanecem disponíveis para detalhe.
"""

CHAVE_CONTRATO_SQL = "COALESCE(registroCge, urlContrato)"


def deduplicar_contratos(conn) -> tuple[int, int]:
    """Substitui `contratos` por versão deduplicada. Retorna (antes, depois)."""
    antes = conn.execute("SELECT COUNT(*) FROM contratos").fetchone()[0]
    conn.execute(f"""
        CREATE OR REPLACE TABLE contratos AS
        SELECT * EXCLUDE (_rn) FROM (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY {CHAVE_CONTRATO_SQL}
                ORDER BY (cnpjCpf IS NOT NULL) DESC,
                         valorTotal DESC NULLS LAST,
                         LENGTH(COALESCE(CAST(aditivo AS VARCHAR), '')) DESC
            ) AS _rn
            FROM contratos
        ) WHERE _rn = 1
    """)
    depois = conn.execute("SELECT COUNT(*) FROM contratos").fetchone()[0]
    return antes, depois


if __name__ == "__main__":
    import sys
    import duckdb

    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/compras_pb.duckdb"
    con = duckdb.connect(db_path)
    a, d = deduplicar_contratos(con)
    print(f"contratos: {a} -> {d} registros ({a - d} duplicados removidos)")
    con.close()

