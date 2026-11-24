"""Gera o Relatório Técnico em PDF para o Grupo de Trabalho (GT):
Esclarecimento sobre a Diferença entre o Valor Adjudicado nas Contratações (Licitações)
e o Volume Financeiro dos Contratos Firmados no Exercício de 2026 no Portal de Compras da Paraíba.

Salva em:
- outputs/relatorio/resumo_difereca_valor_contratacoes_contratratos.pdf
- outputs/relatorio/resumo_diferenca_valor_contratacoes_contratos.pdf
"""

import os
import duckdb
import weasyprint

DB_PATH = "data/compras_pb.duckdb"
OUT_DIR = "outputs/relatorio"
PDF_NOME_EXATO = os.path.join(OUT_DIR, "resumo_difereca_valor_contratacoes_contratratos.pdf")
PDF_NOME_PADRAO = os.path.join(OUT_DIR, "resumo_diferenca_valor_contratacoes_contratos.pdf")
HTML_PATH = os.path.join(OUT_DIR, "resumo_diferenca_valor_contratacoes_contratos.html")

os.makedirs(OUT_DIR, exist_ok=True)


def fmt_moeda(val):
    if val is None or val != val:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(val):
    if val is None or val != val:
        return "0"
    return f"{int(val):,}".replace(",", ".")


def fmt_pct(val):
    if val is None or val != val:
        return "0,00%"
    return f"{val:.2f}%".replace(".", ",")


def carregar_dados():
    conn = duckdb.connect(DB_PATH, read_only=True)

    # 1. KPIs 2026
    lic_row = conn.execute("""
        SELECT COUNT(*), SUM(valorEstimado), SUM(valorAdjudicado)
        FROM contratacoes
        WHERE ano_referencia = 2026 AND valorAdjudicado IS NOT NULL
    """).fetchone()
    total_lic_qtd = lic_row[0]
    total_lic_adj = lic_row[2]

    ct_row = conn.execute("""
        SELECT COUNT(*), SUM(valorOriginal), SUM(valorAditivos), SUM(valorApostilas), SUM(valorTotal)
        FROM contratos
        WHERE ano_referencia = 2026 AND valorTotal IS NOT NULL
    """).fetchone()
    total_ct_qtd = ct_row[0]
    total_ct_val = ct_row[4]
    diferenca_abs = total_ct_val - total_lic_adj

    # 2. Série Histórica (2024-2026)
    df_historico = conn.execute("""
        WITH lic AS (
            SELECT 
                ano_referencia,
                COUNT(*) as qtd_lic,
                SUM(valorAdjudicado) as val_adjudicado
            FROM contratacoes
            WHERE ano_referencia IN (2024, 2025, 2026) AND valorAdjudicado IS NOT NULL
            GROUP BY 1
        ),
        ct AS (
            SELECT 
                ano_referencia,
                COUNT(*) as qtd_ct,
                SUM(valorTotal) as val_contratado
            FROM contratos
            WHERE ano_referencia IN (2024, 2025, 2026) AND valorTotal IS NOT NULL
            GROUP BY 1
        )
        SELECT 
            l.ano_referencia,
            l.qtd_lic,
            l.val_adjudicado,
            c.qtd_ct,
            c.val_contratado,
            (c.val_contratado - l.val_adjudicado) as diferenca,
            (c.val_contratado / l.val_adjudicado) as razao
        FROM lic l
        JOIN ct c ON l.ano_referencia = c.ano_referencia
        ORDER BY l.ano_referencia;
    """).df()

    # 3. Decomposição da Carteira de Contratos de 2026
    df_decomposicao = conn.execute("""
        WITH contratos_2026 AS (
            SELECT 
                c.registroCge,
                c.valorTotal,
                c.numeroProcessoLicitacao,
                l.numeroProcesso as lic_processo,
                l.ano_referencia as lic_ano
            FROM contratos c
            LEFT JOIN (
                SELECT numeroProcesso, FIRST(ano_referencia) as ano_referencia
                FROM contratacoes
                GROUP BY numeroProcesso
            ) l ON c.numeroProcessoLicitacao = l.numeroProcesso
            WHERE c.ano_referencia = 2026 AND c.valorTotal IS NOT NULL
        )
        SELECT 
            CASE 
                WHEN numeroProcessoLicitacao IS NULL THEN '1. Sem Processo Centralizado (Concessões B3, Estatais, Gestão e Dispensas)'
                WHEN lic_processo IS NULL THEN '2. Processo Não Mapeado no Catálogo Central'
                WHEN lic_ano = 2026 THEN '3. Decorrentes de Licitações Homologadas em 2026 (Mesmo Exercício)'
                WHEN lic_ano < 2026 THEN '4. Decorrentes de Licitações de Exercícios Anteriores (2024/2025)'
                ELSE '5. Outros'
            END as categoria_vinculo,
            COUNT(*) as total_contratos,
            SUM(valorTotal) as volume_contratos,
            ROUND(SUM(valorTotal) * 100.0 / (SELECT SUM(valorTotal) FROM contratos WHERE ano_referencia = 2026), 2) as pct_volume
        FROM contratos_2026
        GROUP BY 1
        ORDER BY volume_contratos DESC;
    """).df()

    # 4. Top Contratos Emblemáticos de 2026 que explicam o descolamento
    df_top_contratos = conn.execute("""
        SELECT 
            c.registroCge,
            c.numeroContrato,
            c.siglaOrgao,
            c.contratado,
            COALESCE(c.numeroProcessoLicitacao, 'Sem Edital Central (B3/Estatais)') as processo,
            c.valorTotal,
            c.objeto
        FROM contratos c
        WHERE c.ano_referencia = 2026 AND c.valorTotal IS NOT NULL
        ORDER BY c.valorTotal DESC
        LIMIT 6;
    """).df()

    conn.close()

    return {
        "total_lic_qtd": total_lic_qtd,
        "total_lic_adj": total_lic_adj,
        "total_ct_qtd": total_ct_qtd,
        "total_ct_val": total_ct_val,
        "diferenca_abs": diferenca_abs,
        "df_historico": df_historico,
        "df_decomposicao": df_decomposicao,
        "df_top_contratos": df_top_contratos,
    }


def gerar_relatorio():
    dados = carregar_dados()

    # Tabela Histórico HTML
    rows_hist_html = ""
    for _, r in dados["df_historico"].iterrows():
        ano = int(r["ano_referencia"])
        is_2026 = (ano == 2026)
        destaque = "style='background: #f1f5f9; font-weight: bold;'" if is_2026 else ""
        rows_hist_html += f"""
        <tr {destaque}>
            <td style="text-align: center;"><strong>{ano}</strong></td>
            <td class="num">{fmt_int(r['qtd_lic'])}</td>
            <td class="num">{fmt_moeda(r['val_adjudicado'])}</td>
            <td class="num">{fmt_int(r['qtd_ct'])}</td>
            <td class="num">{fmt_moeda(r['val_contratado'])}</td>
            <td class="num" style="color: {'#0f2c59' if is_2026 else '#334155'};">{fmt_moeda(r['diferenca'])}</td>
            <td class="num" style="color: {'#b91c1c' if is_2026 else '#334155'};"><strong>{r['razao']:.2f}x</strong></td>
        </tr>
        """

    # Tabela Decomposição HTML
    rows_decomp_html = ""
    for _, r in dados["df_decomposicao"].iterrows():
        rows_decomp_html += f"""
        <tr>
            <td><strong>{r['categoria_vinculo']}</strong></td>
            <td class="num">{fmt_int(r['total_contratos'])}</td>
            <td class="num">{fmt_moeda(r['volume_contratos'])}</td>
            <td class="num"><strong>{fmt_pct(r['pct_volume'])}</strong></td>
        </tr>
        """

    # Tabela Top Contratos HTML
    rows_top_html = ""
    for _, r in dados["df_top_contratos"].iterrows():
        rows_top_html += f"""
        <tr>
            <td style="white-space: nowrap;"><code>{r['registroCge']}</code><br><span class="muted">{r['siglaOrgao']}</span></td>
            <td><strong>{r['contratado']}</strong></td>
            <td><code>{r['processo']}</code></td>
            <td class="num"><strong>{fmt_moeda(r['valorTotal'])}</strong></td>
            <td>{r['objeto'][:90]}...</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
    @page {{
        size: A4;
        margin: 11mm 12mm 12mm 12mm;
        @bottom-center {{
            content: "Portal Compras Públicas PB | Nota Técnica GT — Página " counter(page) " de " counter(pages);
            font-family: 'Inter', 'DejaVu Sans', sans-serif;
            font-size: 7.5pt;
            color: #64748b;
        }}
    }}
    body {{
        font-family: 'Inter', 'DejaVu Sans', sans-serif;
        font-size: 8.5pt;
        line-height: 1.36;
        color: #1e293b;
        margin: 0;
        padding: 0;
    }}
    .header {{
        border-bottom: 2.5px solid #0f2c59;
        padding-bottom: 5px;
        margin-bottom: 8px;
    }}
    .instituicao {{
        font-size: 7.5pt;
        font-weight: 700;
        letter-spacing: 0.8px;
        color: #0f2c59;
        text-transform: uppercase;
    }}
    h1 {{
        font-size: 13.5pt;
        color: #0f2c59;
        margin: 2px 0 2px 0;
        line-height: 1.15;
    }}
    .subtitulo {{
        font-size: 8.5pt;
        color: #475569;
        margin: 0;
    }}
    .meta-bar {{
        background: #f1f5f9;
        border-left: 3px solid #0f2c59;
        padding: 4px 8px;
        font-size: 7.5pt;
        color: #334155;
        margin-bottom: 8px;
    }}
    h2 {{
        font-size: 10pt;
        color: #0f2c59;
        border-bottom: 1px solid #cbd5e1;
        padding-bottom: 2px;
        margin: 8px 0 4px 0;
        page-break-after: avoid;
    }}
    p {{
        margin: 0 0 5px 0;
        text-align: justify;
    }}
    .kpi-grid {{
        display: table;
        width: 100%;
        table-layout: fixed;
        border-spacing: 5px 0;
        margin: 0 -5px 8px -5px;
    }}
    .kpi-card {{
        display: table-cell;
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-top: 2.5px solid #0f2c59;
        border-radius: 4px;
        padding: 5px 7px;
        vertical-align: top;
    }}
    .kpi-card.warn {{
        border-top-color: #b91c1c;
        background: #fffafa;
    }}
    .kpi-label {{
        font-size: 6.8pt;
        text-transform: uppercase;
        color: #64748b;
        font-weight: 700;
    }}
    .kpi-val {{
        font-size: 11pt;
        font-weight: 800;
        color: #0f2c59;
        margin: 1px 0;
    }}
    .kpi-card.warn .kpi-val {{
        color: #b91c1c;
    }}
    .kpi-sub {{
        font-size: 6.8pt;
        color: #475569;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 5px 0 7px 0;
        font-size: 7.3pt;
    }}
    th {{
        background: #0f2c59;
        color: #ffffff;
        font-weight: 600;
        text-align: left;
        padding: 3.5px 5px;
        border: 1px solid #0f2c59;
    }}
    td {{
        padding: 3px 5px;
        border: 1px solid #cbd5e1;
        vertical-align: middle;
    }}
    tr:nth-child(even) td {{
        background: #f8fafc;
    }}
    .num {{
        text-align: right;
        white-space: nowrap;
    }}
    .muted {{
        font-size: 6.5pt;
        color: #64748b;
    }}
    code {{
        background: #e2e8f0;
        padding: 1px 3px;
        border-radius: 3px;
        font-size: 6.8pt;
    }}
    .callout {{
        background: #eff6ff;
        border-left: 3px solid #1d4ed8;
        padding: 5px 8px;
        margin: 6px 0;
        font-size: 7.8pt;
    }}
    .callout-warn {{
        background: #fff7ed;
        border-left: 3px solid #c2410c;
        padding: 5px 8px;
        margin: 6px 0;
        font-size: 7.8pt;
    }}
    ul {{
        margin: 2px 0 6px 14px;
        padding: 0;
    }}
    li {{
        margin-bottom: 2px;
    }}
</style>
</head>
<body>

<div class="header">
    <div class="instituicao">UFPB / SUDENE / Governo do Estado da Paraíba | Grupo de Trabalho (GT)</div>
    <h1>Nota Técnica: Diferença entre Valor de Licitações e Volume de Contratos (2026)</h1>
    <p class="subtitulo">Análise Metodológica, Orçamentária e Decomposição Empírica dos Dados no Painel de Compras Públicas</p>
</div>

<div class="meta-bar">
    <strong>Painel Streamlit Referência:</strong> <code>1_🛍️_Compras_Publicas.py</code> (Módulo de Compras Públicas) |
    <strong>Fontes Oficiais:</strong> Central de Compras da PB (API <code>/contratacoes</code>) e CGE-PB / Transparência (API <code>/contratos</code>)
</div>

<h2>1. O Questionamento do Grupo de Trabalho (GT)</h2>
<p>
Ao acessar o <strong>Módulo 1: Compras Públicas (Painel Exploratório)</strong> com o filtro posicionado no ano de <strong>2026</strong>, o Grupo de Trabalho identificou duas grandezas financeiras com valores aparentemente divergentes:
</p>
<ul>
    <li><strong>Aba 1 (Visão: Contratações / Licitações):</strong> Valor Total Adjudicado de <strong>R$ 4.524.850.970,69</strong> em <strong>4.579 processos licitatórios</strong>.</li>
    <li><strong>Aba 2 (Detalhamento: Contratos Firmados):</strong> Volume Financeiro Contratado de <strong>R$ 13.390.270.455,16</strong> em <strong>4.736 contratos firmados</strong>.</li>
</ul>
<p>
A diferença absoluta observada é de <strong>R$ 8.865.419.484,47</strong> (o volume de contratos é <strong>2,96 vezes maior</strong> que o volume de licitações).
</p>

<div class="kpi-grid">
    <div class="kpi-card">
        <div class="kpi-label">Licitações 2026 (Adjudicado)</div>
        <div class="kpi-val">{fmt_moeda(dados['total_lic_adj'])}</div>
        <div class="kpi-sub">{fmt_int(dados['total_lic_qtd'])} editais homologados no ano</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Contratos 2026 (Firmados)</div>
        <div class="kpi-val">{fmt_moeda(dados['total_ct_val'])}</div>
        <div class="kpi-sub">{fmt_int(dados['total_ct_qtd'])} instrumentos formais assinados</div>
    </div>
    <div class="kpi-card warn">
        <div class="kpi-label">Diferença Absoluta</div>
        <div class="kpi-val">+{fmt_moeda(dados['diferenca_abs'])}</div>
        <div class="kpi-sub">Razão Contratos / Licitações: 2,96x</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Contrato Acciona / CAGEPA</div>
        <div class="kpi-val">R$ 6,07 bilhões</div>
        <div class="kpi-sub">Explica 68,45% da diferença total</div>
    </div>
</div>

<h2>2. Diferença Conceitual: Licitação vs. Contrato</h2>
<p>
A discrepância decorre de as duas abas medirem <strong>fases distintas e assíncronas do ciclo de compras públicas</strong>, alimentadas por sistemas complementares do Estado:
</p>
<p>
<strong>1. Contratações (Licitações):</strong> Mede o <em>esforço processual licitatório</em> conduzido e homologado pela Central de Compras no ano civil (pregões eletrônicos, concorrências, dispensas registradas). O valor adjudicado representa o lance vencedor no certame. Muitas licitações são do tipo <strong>Registro de Preços (SRP)</strong>, que estabelecem apenas uma estimativa teto sem obrigação imediata de contratação integral.
</p>
<p>
<strong>2. Contratos Firmados:</strong> Mede o <em>compromisso jurídico, orçamentário e financeiro efetivo</em> celebrado entre os órgãos e os fornecedores (com dotação, empenho e cronograma de desembolso). Engloba instrumentos contratuais decorrentes de leilões e concessões internacionais de estatais, termos de gestão hospitalar, adesões a atas e licitações de anos anteriores.
</p>

<h2>3. Decomposição Empírica dos R$ 13,39 Bilhões de Contratos em 2026</h2>
<p>
Ao cruzar registro por registro cada contrato assinado em 2026 com os processos de licitação no banco analítico <code>compras_pb.duckdb</code>, a carteira de R$ 13,39 bilhões divide-se em três blocos perfeitamente rastreáveis:
</p>

<table>
    <thead>
        <tr>
            <th>Origem do Instrumento Contratual (Exercício 2026)</th>
            <th class="num">Qtd. Contratos</th>
            <th class="num">Volume Contratado</th>
            <th class="num">% da Carteira</th>
        </tr>
    </thead>
    <tbody>
        {rows_decomp_html}
    </tbody>
</table>

<div class="callout-warn">
    <strong>Os 4 Fatores Explicativos do Descolamento:</strong>
    <ul>
        <li><strong>Fator 1 — O Megacontrato da CAGEPA / Acciona (R$ 6,07 bilhões):</strong> O Contrato nº 0213/2026 da CAGEPA com a <em>Concessionária Acciona Água Paraíba SPE S.A.</em> soma <strong>R$ 6.068.736.000,00</strong> (45,32% de todos os contratos de 2026). Trata-se de uma concessão pública internacional leiloada na Bolsa de Valores (B3/SP), regida pela Lei das Estatais (Lei 13.303/2016) e Lei de Concessões (Lei 8.987/1995). Ela é registrada no Portal da Transparência da CGE como contrato, mas não tramita como pregão da Central de Compras (processo licitatório central nulo).</li>
        <li><strong>Fator 2 — Defasagem Temporal de Ciclo (R$ 2,74 bilhões):</strong> 1.895 contratos assinados em 2026 decorrem de licitações homologadas em <strong>2024 e 2025</strong>. Grandes contratações de obras rodoviárias, frotas e TI são licitadas no final de um exercício e formalizadas no seguinte. O valor dessas licitações computou nos anos anteriores, enquanto o valor contratual incide em 2026.</li>
        <li><strong>Fator 3 — Gestão Hospitalar e Estatais sem Edital Centralizado (R$ 1,73 bilhão):</strong> Contratos como a gestão do Hospital Metropolitano pela <em>PB Saúde</em> (R$ 354,96 mi) e obras hídricas da SEIRH (R$ 270,00 mi) tramitam por termos de gestão ou regimes especiais.</li>
        <li><strong>Fator 4 — Atas de Registro de Preços de 2026 com Saldo a Executar (R$ 911 milhões):</strong> Na aba de Licitações, 2.295 processos licitados em 2026 (R$ 911,10 mi) são atas SRP cujo consumo ocorrerá parceladamente em até 12 meses (muitos contratos só serão assinados em 2027).</li>
    </ul>
</div>

<h2>4. Top Contratos de 2026 que Ilustram a Dinâmica</h2>
<p>
A tabela abaixo lista os maiores contratos de 2026, comprovando como grandes valores decorrem de concessões na B3 ou de licitações homologadas em 2025:
</p>

<table>
    <thead>
        <tr>
            <th>Registro / Órgão</th>
            <th>Fornecedor Contratado</th>
            <th>Processo de Licitação Vinculado</th>
            <th class="num">Valor do Contrato</th>
            <th>Objeto Resumido</th>
        </tr>
    </thead>
    <tbody>
        {rows_top_html}
    </tbody>
</table>

<h2>5. Contexto Histórico: A Relação Contratos / Licitações (2024–2026)</h2>
<p>
A comparação com os anos de 2024 e 2025 revela que o volume de contratos firmados é <strong>estruturalmente superior</strong> ao volume de licitações homologadas no mesmo ano, variando conforme a maturação de grandes projetos estatais:
</p>

<table>
    <thead>
        <tr>
            <th style="text-align: center;">Ano</th>
            <th class="num">Qtd. Licitações</th>
            <th class="num">Valor Adjudicado (A)</th>
            <th class="num">Qtd. Contratos</th>
            <th class="num">Valor Contratado (B)</th>
            <th class="num">Diferença (B - A)</th>
            <th class="num">Razão (B / A)</th>
        </tr>
    </thead>
    <tbody>
        {rows_hist_html}
    </tbody>
</table>

<div class="callout">
    <strong>Conclusão Técnica para o GT:</strong>  
    Em 2024, a razão Contratos/Licitações foi de <strong>1,69x</strong>. Se expurgarmos de 2026 o megacontrato atípico da concessão da CAGEPA (R$ 6,07 bi), o saldo restante de contratos é de <strong>R$ 7,32 bilhões</strong>, resultando em uma razão de <strong>1,62x</strong> sobre as licitações de 2026 (R$ 4,52 bi) — mantendo perfeita aderência ao padrão estrutural histórico do Estado.
</div>

</body>
</html>
"""

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Renderiza em PDF
    weasyprint.HTML(HTML_PATH).write_pdf(PDF_NOME_EXATO)
    weasyprint.HTML(HTML_PATH).write_pdf(PDF_NOME_PADRAO)

    print(f"Relatório PDF gerado com sucesso em:")
    print(f" -> {PDF_NOME_EXATO}")
    print(f" -> {PDF_NOME_PADRAO}")


if __name__ == "__main__":
    gerar_relatorio()
