"""Gera o Relatório Técnico 02 em PDF para o Grupo de Trabalho (GT):
Análise Descritiva das Grandes Categorias Econômicas do IBGE (Tabela 8889 SIDRA / PIM-PF)
nas Compras Públicas da Paraíba com referência ao ano de 2026.

Compara as duas abordagens metodológicas:
- Abordagem 1: Indústria Fabricante Estrita (PIM-PF / Seções B e C da CNAE)
- Abordagem 2: Cadeia Ampla de Aquisição de Bens (Indústria + Comércio Distribuidor)
Sem inclusão de códigos SQL no corpo do relatório.
"""

import os
import duckdb
import weasyprint

DB_PATH = "data/compras_pb.duckdb"

def formatar_moeda(val):
    if val is None or val != val:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_int(val):
    if val is None or val != val:
        return "0"
    return f"{int(val):,}".replace(",", ".")

def carregar_dados_2026():
    conn = duckdb.connect(DB_PATH, read_only=True)
    
    # Total geral 2026
    total_row = conn.execute("""
        SELECT COUNT(DISTINCT registroCge), SUM(valorTotal)
        FROM contratos 
        WHERE ano_referencia = 2026 AND valorTotal IS NOT NULL
    """).fetchone()
    total_contratos_2026 = total_row[0]
    total_valor_2026 = total_row[1]

    # Abordagem 1: Indústria Estrita (PIM-PF)
    sql_ind = """
    WITH fornecedores_cgce_industria AS (
        SELECT 
            cnpj,
            cnae_fiscal,
            cnae_descricao,
            CASE
                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 28
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 26 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (261, 262, 265))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 27 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (271, 273, 279))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (292, 293))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 30 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (301, 303, 304, 305))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 100) AS INT) = 32501)
                     OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 33
                     THEN 'Bens de Capital'

                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) BETWEEN 5 AND 9
                     OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) IN (16, 17, 22, 23, 24, 25)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 20 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) NOT IN (206, 207))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 294)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 13 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (131, 132, 133))
                     THEN 'Bens Intermediários'

                WHEN (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 26 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (263, 264))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 27 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 275)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 291)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 30 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 309)
                     OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 31
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (321, 322, 323, 324))
                     THEN 'Bens de Consumo Duráveis'

                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) IN (10, 11, 12, 14, 15, 18, 21)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 13 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (134, 135))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 20 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (206, 207))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 329)
                     THEN 'Bens de Consumo Semiduráveis e Não Duráveis'
                ELSE NULL
            END AS categoria_ibge_pim
        FROM dim_fornecedores_cnae
        WHERE CAST(FLOOR(cnae_fiscal / 100000) AS INT) BETWEEN 5 AND 33
    )
    SELECT 
        f.categoria_ibge_pim,
        COUNT(DISTINCT c.registroCge) as total_contratos,
        SUM(c.valorTotal) as volume_financeiro_total
    FROM contratos c
    JOIN fornecedores_cgce_industria f 
        ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = LPAD(CAST(CAST(f.cnpj AS BIGINT) AS VARCHAR), 14, '0')
    WHERE c.ano_referencia = 2026 AND c.valorTotal IS NOT NULL AND f.categoria_ibge_pim IS NOT NULL
    GROUP BY 1
    ORDER BY volume_financeiro_total DESC;
    """
    df_ind_2026 = conn.execute(sql_ind).df()

    # Abordagem 2: Cadeia Ampla de Compras
    sql_ampla = """
    WITH fornecedores_cgce_amplo AS (
        SELECT 
            cnpj,
            cnae_fiscal,
            cnae_descricao,
            CASE
                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 28
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 26 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (261, 262, 265))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 27 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (271, 273, 279))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (292, 293))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 30 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (301, 303, 304, 305))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 100) AS INT) = 32501)
                     OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 33
                     OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (466, 465)
                     OR CAST(FLOOR(cnae_fiscal / 100) AS INT) = 47512
                     OR cnae_fiscal IN (4511102, 4511104, 4511106)
                     THEN 'Bens de Capital'

                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) BETWEEN 5 AND 9
                     OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) IN (16, 17, 22, 23, 24, 25)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 20 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) NOT IN (206, 207))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 294)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 13 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (131, 132, 133))
                     OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (453, 467, 468)
                     OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 474
                     THEN 'Bens Intermediários'

                WHEN (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 26 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (263, 264))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 27 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 275)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 291)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 30 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 309)
                     OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 31
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (321, 322, 323, 324))
                     OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 454
                     OR CAST(FLOOR(cnae_fiscal / 100) AS INT) IN (47539, 47547, 46494)
                     OR cnae_fiscal IN (4511101, 4511103, 4511105)
                     THEN 'Bens de Consumo Duráveis'

                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) IN (10, 11, 12, 14, 15, 18, 21)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 13 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (134, 135))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 20 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (206, 207))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 329)
                     OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (462, 463, 464, 471, 472, 473, 476, 477, 478)
                     THEN 'Bens de Consumo Semiduráveis e Não Duráveis'

                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) BETWEEN 41 AND 43 THEN 'Construção Civil (Infraestrutura/FBCF)'
                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) BETWEEN 35 AND 39 THEN 'Serviços Industriais de Utilidade Pública (SIUP)'
                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) BETWEEN 49 AND 96 THEN 'Serviços Gerais'
                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) BETWEEN 1 AND 3 THEN 'Agropecuária'
                ELSE 'Demais Setores'
            END AS macrocategoria_economica
        FROM dim_fornecedores_cnae
    )
    SELECT 
        f.macrocategoria_economica,
        COUNT(DISTINCT c.registroCge) AS total_contratos,
        SUM(c.valorTotal) AS volume_financeiro_total
    FROM contratos c
    LEFT JOIN fornecedores_cgce_amplo f 
        ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = LPAD(CAST(CAST(f.cnpj AS BIGINT) AS VARCHAR), 14, '0')
    WHERE c.ano_referencia = 2026 AND c.valorTotal IS NOT NULL
    GROUP BY 1
    ORDER BY volume_financeiro_total DESC;
    """
    df_ampla_2026 = conn.execute(sql_ampla).df()

    # Exemplos de contratos por categoria em 2026
    sql_amostra = """
    WITH fornecedores_cgce_amplo AS (
        SELECT 
            cnpj,
            cnae_fiscal,
            cnae_descricao,
            CASE
                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 28
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 26 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (261, 262, 265))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 27 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (271, 273, 279))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (292, 293))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 30 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (301, 303, 304, 305))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 100) AS INT) = 32501)
                     OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 33
                     OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (466, 465)
                     OR CAST(FLOOR(cnae_fiscal / 100) AS INT) = 47512
                     OR cnae_fiscal IN (4511102, 4511104, 4511106)
                     THEN 'Bens de Capital'

                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) BETWEEN 5 AND 9
                     OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) IN (16, 17, 22, 23, 24, 25)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 20 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) NOT IN (206, 207))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 294)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 13 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (131, 132, 133))
                     OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (453, 467, 468)
                     OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 474
                     THEN 'Bens Intermediários'

                WHEN (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 26 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (263, 264))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 27 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 275)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 291)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 30 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 309)
                     OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 31
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (321, 322, 323, 324))
                     OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 454
                     OR CAST(FLOOR(cnae_fiscal / 100) AS INT) IN (47539, 47547, 46494)
                     OR cnae_fiscal IN (4511101, 4511103, 4511105)
                     THEN 'Bens de Consumo Duráveis'

                WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) IN (10, 11, 12, 14, 15, 18, 21)
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 13 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (134, 135))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 20 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (206, 207))
                     OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 329)
                     OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (462, 463, 464, 471, 472, 473, 476, 477, 478)
                     THEN 'Bens de Consumo Semiduráveis e Não Duráveis'
                ELSE 'Outros'
            END AS macrocategoria_economica
        FROM dim_fornecedores_cnae
    )
    SELECT 
        f.macrocategoria_economica,
        c.contratado,
        c.nomeOrgao,
        c.objeto,
        c.valorTotal
    FROM contratos c
    JOIN fornecedores_cgce_amplo f 
      ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = LPAD(CAST(CAST(f.cnpj AS BIGINT) AS VARCHAR), 14, '0')
    WHERE c.ano_referencia = 2026 AND f.macrocategoria_economica IN ('Bens de Capital', 'Bens Intermediários', 'Bens de Consumo Duráveis', 'Bens de Consumo Semiduráveis e Não Duráveis')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY f.macrocategoria_economica ORDER BY c.valorTotal DESC) <= 3
    ORDER BY f.macrocategoria_economica, c.valorTotal DESC;
    """
    df_amostra = conn.execute(sql_amostra).df()
    
    conn.close()
    return total_contratos_2026, total_valor_2026, df_ind_2026, df_ampla_2026, df_amostra

def gerar_html(total_contratos_2026, total_valor_2026, df_ind, df_ampla, df_amostra):
    total_val_ind = df_ind['volume_financeiro_total'].sum()
    total_ct_ind = df_ind['total_contratos'].sum()

    total_val_bens_amplo = df_ampla[df_ampla['macrocategoria_economica'].str.contains('Bens')]['volume_financeiro_total'].sum()
    total_ct_bens_amplo = df_ampla[df_ampla['macrocategoria_economica'].str.contains('Bens')]['total_contratos'].sum()

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório Técnico 02 - Análise de Grandes Categorias Econômicas (IBGE/PIM-PF 2026)</title>
<style>
    @page {{
        size: A4 portrait;
        margin: 15mm 15mm 15mm 15mm;
        @bottom-right {{
            content: "Página " counter(page) " de " counter(pages);
            font-size: 8pt;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #7f8c8d;
        }}
        @bottom-left {{
            content: "Portal Compras Públicas PB | Relatório Técnico 02 - Grupo de Trabalho (GT)";
            font-size: 8pt;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #7f8c8d;
        }}
    }}
    
    body {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #2c3e50;
        line-height: 1.45;
        font-size: 9.5pt;
    }}

    .header-box {{
        border-bottom: 2px solid #2980b9;
        padding-bottom: 12px;
        margin-bottom: 16px;
    }}
    
    .institucional {{
        font-size: 8.5pt;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #7f8c8d;
        font-weight: bold;
        margin-bottom: 4px;
    }}

    h1 {{
        font-size: 15pt;
        color: #1a365d;
        margin: 6px 0 4px 0;
        line-height: 1.25;
    }}

    .subtitle {{
        font-size: 10pt;
        color: #4a5568;
        font-weight: 500;
        margin-bottom: 6px;
    }}

    .meta-date {{
        font-size: 8.5pt;
        color: #718096;
    }}

    .card-kpi-container {{
        display: flex;
        flex-direction: row;
        gap: 10px;
        margin-bottom: 16px;
    }}

    .kpi-card {{
        flex: 1;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #3182ce;
        border-radius: 4px;
        padding: 8px 10px;
    }}

    .kpi-title {{
        font-size: 7.5pt;
        text-transform: uppercase;
        color: #64748b;
        font-weight: bold;
        margin-bottom: 2px;
    }}

    .kpi-value {{
        font-size: 12.5pt;
        font-weight: bold;
        color: #1e293b;
    }}

    .kpi-sub {{
        font-size: 7.5pt;
        color: #059669;
        font-weight: 600;
    }}

    h2 {{
        font-size: 11.5pt;
        color: #1e3a8a;
        border-bottom: 1.5px solid #e2e8f0;
        padding-bottom: 4px;
        margin-top: 16px;
        margin-bottom: 8px;
        page-break-after: avoid;
    }}

    h3 {{
        font-size: 9.5pt;
        color: #2b6cb0;
        margin-top: 12px;
        margin-bottom: 6px;
        page-break-after: avoid;
    }}

    p {{
        margin: 0 0 8px 0;
        text-align: justify;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 8px 0 12px 0;
        font-size: 8pt;
        page-break-inside: avoid;
    }}

    th {{
        background-color: #2b6cb0;
        color: #ffffff;
        font-weight: 600;
        text-align: left;
        padding: 5px 6px;
        border: 1px solid #2b6cb0;
    }}

    td {{
        padding: 4px 6px;
        border: 1px solid #e2e8f0;
    }}

    tr:nth-child(even) td {{
        background-color: #f8fafc;
    }}

    .text-right {{
        text-align: right;
    }}

    .text-center {{
        text-align: center;
    }}

    .badge-cat {{
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 2px 5px;
        border-radius: 3px;
        font-weight: bold;
        font-size: 7.5pt;
    }}

    .box-destaque {{
        background-color: #eff6ff;
        border-left: 4px solid #2563eb;
        padding: 8px 12px;
        margin: 10px 0;
        font-size: 8.5pt;
        border-radius: 2px;
    }}

    .box-alerta {{
        background-color: #fffbeb;
        border-left: 4px solid #d97706;
        padding: 8px 12px;
        margin: 10px 0;
        font-size: 8.5pt;
        border-radius: 2px;
    }}

    .page-break {{
        page-break-before: always;
    }}
</style>
</head>
<body>

<div class="header-box">
    <div class="institucional">UFPB / SUDENE / Governo do Estado da Paraíba | Grupo de Trabalho (GT)</div>
    <h1>Relatório Técnico 02: Grandes Categorias Econômicas (IBGE / PIM-PF)</h1>
    <div class="subtitle">Análise Descritiva e Diferenciação entre Indústria Fabricante Estrita e Cadeia Ampla de Bens nas Compras Públicas Estaduais (Exercício 2026)</div>
    <div class="meta-date">Referência Temporal: Exercício 2026 | Fonte: Tabela 8889 SIDRA/IBGE, Central de Compras PB e CGE-PB</div>
</div>

<div class="card-kpi-container">
    <div class="kpi-card">
        <div class="kpi-title">Orçamento Total 2026</div>
        <div class="kpi-value">{formatar_moeda(total_valor_2026)}</div>
        <div class="kpi-sub">{formatar_int(total_contratos_2026)} Contratos Firmados</div>
    </div>
    <div class="kpi-card" style="border-left-color: #16a34a;">
        <div class="kpi-title">Indústria Fabricante (PIM-PF)</div>
        <div class="kpi-value">{formatar_moeda(total_val_ind)}</div>
        <div class="kpi-sub">{formatar_int(total_ct_ind)} Contratos Diretos</div>
    </div>
    <div class="kpi-card" style="border-left-color: #d97706;">
        <div class="kpi-title">Cadeia Ampla de Bens</div>
        <div class="kpi-value">{formatar_moeda(total_val_bens_amplo)}</div>
        <div class="kpi-sub">{formatar_int(total_ct_bens_amplo)} Contratos (Indústria + Comércio)</div>
    </div>
    <div class="kpi-card" style="border-left-color: #9333ea;">
        <div class="kpi-title">Bens de Capital (2026)</div>
        <div class="kpi-value">{formatar_moeda(df_ampla.loc[df_ampla['macrocategoria_economica']=='Bens de Capital', 'volume_financeiro_total'].values[0])}</div>
        <div class="kpi-sub">Investimentos / FBCF em Bens</div>
    </div>
</div>

<h2>1. Introdução e Contexto Metodológico</h2>
<p>
Este relatório atende à solicitação do <strong>Grupo de Trabalho (GT)</strong> quanto à viabilidade de classificar e filtrar as compras públicas do Estado da Paraíba a partir das <strong>Grandes Categorias Econômicas</strong> preconizadas pelo IBGE, especificamente estruturadas na <strong>Tabela 8889 do Sistema SIDRA</strong> (Pesquisa Industrial Mensal - Produção Física, PIM-PF).
</p>
<p>
A taxonomia de Categorias de Uso do IBGE divide a produção de bens industriais em quatro eixos macroeconômicos fundamentais:
</p>
<ol>
    <li><strong>Bens de Capital:</strong> Máquinas, equipamentos, aparelhos elétricos pesados, veículos de carga e transporte coletivo, computadores e instrumentos de precisão utilizados para produzir outros bens e serviços (ativos fixos);</li>
    <li><strong>Bens Intermediários:</strong> Insumos manufaturados, peças, partes e matérias-primas que sofrem transformação física na cadeia produtiva (químicos, derivados de petróleo para uso industrial, embalagens, tecidos, cimento, chapas de aço, autopeças);</li>
    <li><strong>Bens de Consumo Duráveis:</strong> Produtos acabados de longa vida útil destinados ao uso final (mobiliário, eletrodomésticos, automóveis de passeio, motocicletas, eletrônicos pessoais);</li>
    <li><strong>Bens de Consumo Semiduráveis e Não Duráveis:</strong> Artigos de consumo corrente ou ciclo curto (produtos farmacêuticos e medicamentos, gêneros alimentícios, combustíveis de consumo final, artigos de limpeza, vestuário, calçados e material hospitalar descartável).</li>
</ol>

<div class="box-destaque">
    <strong>Viabilidade na Base de Dados:</strong> O cruzamento é 100% operacional no projeto, pois cada fornecedor contratado possui seu código oficial <code>cnae_fiscal</code> (7 dígitos) identificado e validado junto à Receita Federal, permitindo alocar os contratos em cada uma das divisões industriais e comerciais correspondentes.
</div>

<h2>2. A Diferenciação Conceitual entre as Duas Abordagens</h2>
<p>
Para interpretar com fidelidade a aplicação dos recursos públicos estaduais no exercício de 2026, é imperativo distinguir com clareza duas perspectivas econômicas complementares:
</p>

<h3>Abordagem 1: Indústria Fabricante Estrita (Escopo PIM-PF / IBGE)</h3>
<p>
Esta abordagem restringe o universo de análise <strong>única e exclusivamente aos fornecedores cuja atividade principal é a indústria fabril</strong> (Seções B e C da CNAE, Divisões 05 a 33). Ela reflete exatamente o recorte metodológico da PIM-PF do IBGE, medindo quanto o Governo do Estado compra <em>diretamente das fábricas e indústrias produtoras</em>.
</p>

<h3>Abordagem 2: Cadeia Ampla de Fornecimento de Bens (Indústria + Comércio Distribuidor)</h3>
<p>
Na administração pública real, a maior parte dos suprimentos e equipamentos não é faturada pela planta fabril, mas sim por <strong>empresas atacadistas, distribuidoras e revendedoras autorizadas</strong> (Seção G da CNAE, Divisões 45 a 47). Esta abordagem reúne os fabricantes industriais e o comércio distribuidor especializado de cada setor (ex.: distribuidoras hospitalares fornecendo medicamentos em Não Duráveis; revendedoras de máquinas e informática em Bens de Capital). Ela expressa o <strong>poder de compra total do Estado direcionado a bens materiais</strong>.
</p>



<h2>3. Abordagem 1: Resultados da Indústria Fabricante Estrita (Exercício 2026)</h2>
<p>
No exercício de 2026, foram identificados <strong>360 contratos</strong> firmados diretamente com indústrias extrativas e de transformação, perfazendo um montante global de <strong>R$ 356.892.589,72</strong>. A tabela abaixo resume a distribuição desse valor pelas 4 categorias industriais do IBGE:
</p>

<table>
    <thead>
        <tr>
            <th>Grande Categoria Econômica (IBGE PIM-PF)</th>
            <th class="text-center">Contratos</th>
            <th class="text-right">Volume Financeiro 2026 (R$)</th>
            <th class="text-right">Part. na Indústria (%)</th>
        </tr>
    </thead>
    <tbody>
"""

    for _, r in df_ind.iterrows():
        pct = (r['volume_financeiro_total'] / total_val_ind * 100) if total_val_ind > 0 else 0
        html += f"""
        <tr>
            <td><span class="badge-cat">{r['categoria_ibge_pim']}</span></td>
            <td class="text-center">{formatar_int(r['total_contratos'])}</td>
            <td class="text-right">{formatar_moeda(r['volume_financeiro_total'])}</td>
            <td class="text-right">{pct:.2f}%</td>
        </tr>
        """

    html += f"""
        <tr style="font-weight: bold; background-color: #edf2f7;">
            <td>TOTAL INDÚSTRIA FABRICANTE DIRETA</td>
            <td class="text-center">{formatar_int(total_ct_ind)}</td>
            <td class="text-right">{formatar_moeda(total_val_ind)}</td>
            <td class="text-right">100,00%</td>
        </tr>
    </tbody>
</table>

<p>
<strong>Destaques da Indústria Direta em 2026:</strong>
</p>
<ul>
    <li><strong>Liderança dos Bens de Capital (30,69%):</strong> O Estado comprou diretamente de indústrias fabris R$ 109,52 milhões em máquinas, equipamentos de telecomunicação e radiocomunicação policial, computadores e equipamentos de medição de água/esgoto;</li>
    <li><strong>Força dos Bens Intermediários (28,93%):</strong> Compras diretas de indústrias químicas (cloro e insumos de tratamento de água para a CAGEPA), asfalto, brita, tubulações de concreto e produtos de borracha/plástico somaram R$ 103,22 milhões;</li>
    <li><strong>Bens de Consumo Semiduráveis e Não Duráveis (18,00%):</strong> Contratação de laboratórios farmacêuticos, indústrias têxteis/fardamentos e gráficas editoriais representou R$ 64,24 milhões;</li>
    <li><strong>Bens de Consumo Duráveis (13,99%):</strong> Aquisição de mobiliário escolar e corporativo padronizado diretamente de fábricas moveleiras somou R$ 49,92 milhões.</li>
</ul>

<h2>4. Abordagem 2: Resultados da Cadeia Ampla de Compras (Exercício 2026)</h2>
<p>
Ao expandir a ótica para abranger a totalidade das compras do Estado em 2026 (incluindo o comércio distribuidor de bens e os contratos de serviços/obras), observa-se que a aquisição de bens físicos alcança <strong>R$ 1,07 bilhão (2.311 contratos)</strong>, distribuída no panorama orçamentário geral:
</p>

<table>
    <thead>
        <tr>
            <th>Macrocategoria Econômica</th>
            <th class="text-center">Contratos</th>
            <th class="text-right">Volume Financeiro 2026 (R$)</th>
            <th class="text-right">Part. no Total (%)</th>
        </tr>
    </thead>
    <tbody>
"""

    for _, r in df_ampla.iterrows():
        pct = (r['volume_financeiro_total'] / total_valor_2026 * 100) if total_valor_2026 > 0 else 0
        destaque = "style='font-weight: bold; background-color: #f0fdf4;'" if "Bens" in str(r['macrocategoria_economica']) else ""
        html += f"""
        <tr {destaque}>
            <td>{r['macrocategoria_economica']}</td>
            <td class="text-center">{formatar_int(r['total_contratos'])}</td>
            <td class="text-right">{formatar_moeda(r['volume_financeiro_total'])}</td>
            <td class="text-right">{pct:.2f}%</td>
        </tr>
        """

    html += f"""
        <tr style="font-weight: bold; background-color: #edf2f7;">
            <td>TOTAL GERAL CONTRATADO EM 2026</td>
            <td class="text-center">{formatar_int(total_contratos_2026)}</td>
            <td class="text-right">{formatar_moeda(total_valor_2026)}</td>
            <td class="text-right">100,00%</td>
        </tr>
    </tbody>
</table>

<div class="box-alerta">
    <strong>Leitura Econômica Estrutural de 2026:</strong> O exercício de 2026 é fortemente marcado por grandes projetos de infraestrutura hídrica e saneamento — notadamente o contrato de concessão de esgotamento sanitário da CAGEPA (Acciona Água / SIUP, R$ 6,07 bi) e grandes obras rodoviárias e adutoras (Construção Civil, R$ 3,31 bi). Juntos, SIUP e Construção Civil absorvem <strong>70,33% do orçamento de 2026</strong>.
</div>



<h2>5. Análise Descritiva dos Bens Adquiridos por Categoria (Casos Concretos de 2026)</h2>
<p>
Para elucidar a natureza dos bens contratados sob cada uma das quatro grandes categorias em 2026, destacam-se os principais contratos e fornecedores registrados na base:
</p>

<h3>A) Bens de Capital (R$ 215,30 milhões na cadeia ampla / R$ 109,52 milhões fabril)</h3>
<p>
Compreende os investimentos em ampliação da capacidade produtiva e modernização tecnológica dos órgãos públicos estaduais.
</p>
<ul>
    <li><strong>Equipamentos de TI para Educação:</strong> <em>Positivo Tecnologia S.A.</em> (Contrato no valor de <strong>R$ 47,19 milhões</strong> com a Secretaria de Estado da Educação para fornecimento de computadores, tablets e equipamentos computacionais);</li>
    <li><strong>Sistemas de Radiocomunicação Segura:</strong> <em>Motorola Solutions Ltda</em> (Contrato de <strong>R$ 22,12 milhões</strong> com a Secretaria de Segurança Pública para terminais e estações de radiocomunicação digital);</li>
    <li><strong>Equipamentos de Medição e Telemetria:</strong> <em>Saga Medição S.A.</em> (Contrato de <strong>R$ 14,08 milhões</strong> com a CAGEPA para aquisição de hidrômetros e equipamentos de macromedição de vazão).</li>
</ul>

<h3>B) Bens de Consumo Semiduráveis e Não Duráveis (R$ 599,24 milhões na cadeia ampla)</h3>
<p>
Constitui o maior volume financeiro de bens de consumo do Estado, concentrado fortemente em saúde pública e assistência hospitalar.
</p>
<ul>
    <li><strong>Medicamentos e Insumos Hospitalares:</strong> Fornecimentos especializados por distribuidoras farmacêuticas como <em>PMH Produtos Médicos Hospitalares Ltda</em> (<strong>R$ 42,43 milhões</strong>), <em>Vision Médica Ltda</em> (<strong>R$ 37,95 milhões</strong>) e <em>Onco Prod Distribuidora</em> (<strong>R$ 35,58 milhões</strong>) para abastecimento das redes hospitalares da Secretaria de Estado da Saúde;</li>
    <li><strong>Alimentação e Nutrição:</strong> Aquisições de gêneros alimentícios e fardamentos escolares sob compras corporativas centralizadas.</li>
</ul>

<h3>C) Bens Intermediários (R$ 153,76 milhões na cadeia ampla / R$ 103,22 milhões fabril)</h3>
<p>
Compreende os insumos químicos, materiais estruturais e peças indispensáveis ao funcionamento dos serviços de utilidade pública e manutenção viária.
</p>
<ul>
    <li><strong>Tratamento e Potabilização de Água:</strong> <em>Tecnosan Projetos e Soluções Ambientais Ltda</em> (dois contratos somando <strong>R$ 24,44 milhões</strong> com a CAGEPA para insumos de tratamento de água e saneamento);</li>
    <li><strong>Química Industrial:</strong> <em>Sabará Químicos e Ingredientes S/A</em> (Contrato de <strong>R$ 6,66 milhões</strong> com a CAGEPA para fornecimento de cloro e coagulantes);</li>
    <li><strong>Materiais de Construção e Asfalto:</strong> Insumos de brita, emulsão asfáltica e tubulações para obras estaduais.</li>
</ul>

<h3>D) Bens de Consumo Duráveis (R$ 99,99 milhões na cadeia ampla / R$ 49,92 milhões fabril)</h3>
<p>
Focado primariamente no aparelhamento físico das escolas e unidades administrativas.
</p>
<ul>
    <li><strong>Mobiliário Escolar e Carteiras:</strong> Contratações diretas de indústrias moveleiras especializadas, como <em>Incomel Indústria de Móveis Ltda</em> (<strong>R$ 15,35 milhões</strong>), <em>Solução Indústria e Comércio de Móveis Ltda</em> (<strong>R$ 14,44 milhões</strong>) e <em>Indústria e Comércio Móveis Kutz Ltda</em> (<strong>R$ 9,96 milhões</strong>), destinadas ao reaparelhamento das escolas da rede estadual de ensino.</li>
</ul>

<h2>6. Conclusões e Encaminhamentos para o Grupo de Trabalho (GT)</h2>
<ol>
    <li><strong>Aderência às Metodologias do IBGE:</strong> A base analítica do portal demonstrou capacidade integral de responder à categorização de bens da Tabela 8889 do SIDRA, sem perda de granularidade;</li>
    <li><strong>Recomendação de Apresentação Dual:</strong> Recomenda-se apresentar ao GT ambas as abordagens: a <em>Indústria Estrita (PIM-PF)</em> para análises de encadeamento produtivo manufatureiro local e a <em>Cadeia Ampla de Bens</em> para monitoramento orçamentário das compras públicas;</li>
    <li><strong>Pendência Registrada no Projeto:</strong> A funcionalidade de filtro dinâmico por Grandes Categorias Econômicas (Bens de Capital, Intermediários, Duráveis e Não Duráveis) foi formalmente registrada como pendência no projeto, aguardando validação do Grupo de Trabalho para implantação no Módulo 5 do Streamlit.</li>
</ol>

<hr style="border: 0; border-top: 1px solid #cbd5e1; margin-top: 20px;">
<div style="font-size: 8pt; color: #64748b; text-align: center;">
    Relatório Técnico 02 elaborado pelo Núcleo de Inteligência e Big Data (NIB / UFPB / SUDENE).<br>
    Coordenação Geral: Prof. Dr. Paulo Fernando Cavalcanti.
</div>

</body>
</html>
"""
    return html

def main():
    print("Conectando ao banco e processando dados de 2026...")
    total_ct, total_val, df_ind, df_ampla, df_amostra = carregar_dados_2026()
    
    print("Gerando HTML do Relatório Técnico 02...")
    html_content = gerar_html(total_ct, total_val, df_ind, df_ampla, df_amostra)
    
    html_path = "outputs/relatorio/relatorio_analise_gt_compras_02.html"
    pdf_path = "outputs/relatorio/relatorio_analise_gt_compras_02.pdf"
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML salvo em: {html_path}")

    print("Renderizando PDF via WeasyPrint...")
    weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
    print(f"PDF gerado com sucesso em: {pdf_path}")

if __name__ == "__main__":
    main()
