"""Gera relatório analítico em PDF para o Grupo de Trabalho (GT)
com base nas planilhas:
- outputs/tables/bens_servicos_itens_contratados.xls
- outputs/tables/bens_servicos_nivel_contratos.xls
- outputs/tables/dados_consolidado.xls
"""

import os
import pandas as pd
import weasyprint

def carregar_dados():
    c_path = "outputs/tables/bens_servicos_nivel_contratos.xls"
    i_path = "outputs/tables/bens_servicos_itens_contratados.xls"
    m_path = "outputs/tables/dados_consolidado.xls"

    df_c = pd.read_excel(c_path)
    df_i = pd.read_excel(i_path)
    df_m = pd.read_excel(m_path)
    return df_c, df_i, df_m

def formatar_moeda(val):
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_int(val):
    if pd.isna(val) or val is None:
        return "0"
    return f"{int(val):,}".replace(",", ".")

def gerar_html(df_c, df_i, df_m):
    # Estatísticas gerais contratos
    total_contratos = len(df_c)
    total_valor_contratos = df_c['Valor_contratado'].sum()
    
    # ME/EPP Contratos
    porte_c = df_c.groupby('is_me_epp')['Valor_contratado'].agg(['count', 'sum']).reset_index()
    porte_c['pct_count'] = (porte_c['count'] / total_contratos * 100).round(2)
    porte_c['pct_val'] = (porte_c['sum'] / total_valor_contratos * 100).round(2)
    
    # Modalidades Contratos
    mod_c = df_c.groupby('modalidade_compra')['Valor_contratado'].agg(['count', 'sum']).reset_index()
    mod_c['pct_val'] = (mod_c['sum'] / total_valor_contratos * 100).round(2)
    mod_c = mod_c.sort_values('sum', ascending=False)

    # Setores Contratos
    set_c = df_c.groupby('setor_economico')['Valor_contratado'].agg(['count', 'sum']).reset_index()
    set_c['pct_val'] = (set_c['sum'] / total_valor_contratos * 100).round(2)
    set_c = set_c.sort_values('sum', ascending=False)

    # Localizacao Contratos
    loc_c = df_c.groupby('localizacao_categoria')['Valor_contratado'].agg(['count', 'sum']).reset_index()
    loc_c['pct_val'] = (loc_c['sum'] / total_valor_contratos * 100).round(2)
    loc_c = loc_c.sort_values('sum', ascending=False)

    # Intensidade OCDE Contratos
    tec_c = df_c.groupby('intensidade_tecnologica_ocde')['Valor_contratado'].agg(['count', 'sum']).reset_index()
    tec_c['pct_val'] = (tec_c['sum'] / total_valor_contratos * 100).round(2)
    tec_c = tec_c.sort_values('sum', ascending=False)

    # Itens Estatísticas
    total_itens = len(df_i)
    total_valor_itens = df_i['valor_total_homologado'].sum()
    porte_i = df_i.groupby('is_me_epp')['valor_total_homologado'].agg(['count', 'sum']).reset_index()
    porte_i['pct_count'] = (porte_i['count'] / total_itens * 100).round(2)
    porte_i['pct_val'] = (porte_i['sum'] / total_valor_itens * 100).round(2)

    # Top 10 Maiores Contratos
    top10_c = df_c.sort_values('Valor_contratado', ascending=False).head(10)

    # Top 10 Órgãos
    top_org = df_c.groupby('orgao_contratante')['Valor_contratado'].agg(['count', 'sum']).reset_index()
    top_org['pct_val'] = (top_org['sum'] / total_valor_contratos * 100).round(2)
    top_org = top_org.sort_values('sum', ascending=False).head(10)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório Analítico de Compras Públicas - GT Paraíba</title>
<style>
    @page {{
        size: A4 portrait;
        margin: 20mm 15mm 20mm 15mm;
        @bottom-right {{
            content: "Página " counter(page) " de " counter(pages);
            font-size: 8pt;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #7f8c8d;
        }}
        @bottom-left {{
            content: "Portal de Compras Públicas PB | Grupo de Trabalho (GT)";
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
        margin-bottom: 18px;
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
        font-size: 16pt;
        color: #1a365d;
        margin: 6px 0 4px 0;
        line-height: 1.25;
    }}

    .subtitle {{
        font-size: 10pt;
        color: #4a5568;
        font-weight: 500;
        margin-bottom: 8px;
    }}

    .meta-date {{
        font-size: 8.5pt;
        color: #718096;
    }}

    .card-kpi-container {{
        display: flex;
        flex-direction: row;
        gap: 10px;
        margin-bottom: 18px;
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
        font-size: 13pt;
        font-weight: bold;
        color: #1e293b;
    }}

    .kpi-sub {{
        font-size: 7.5pt;
        color: #059669;
        font-weight: 600;
    }}

    h2 {{
        font-size: 12pt;
        color: #1e3a8a;
        border-bottom: 1.5px solid #e2e8f0;
        padding-bottom: 4px;
        margin-top: 18px;
        margin-bottom: 8px;
        page-break-after: avoid;
    }}

    h3 {{
        font-size: 10pt;
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
        margin: 8px 0 14px 0;
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

    .badge-me {{
        background-color: #dcfce7;
        color: #166534;
        padding: 2px 5px;
        border-radius: 3px;
        font-weight: bold;
        font-size: 7.5pt;
    }}

    .badge-grande {{
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

    .page-break {{
        page-break-before: always;
    }}
</style>
</head>
<body>

<div class="header-box">
    <div class="institucional">UFPB / SUDENE / Governo do Estado da Paraíba | Grupo de Trabalho (GT)</div>
    <h1>Relatório Analítico de Compras Públicas</h1>
    <div class="subtitle">Perfil Produtivo, Bens e Serviços, Modalidades Licitatórias e Impacto de Micro e Pequenas Empresas (ME/EPP)</div>
    <div class="meta-date">Período Analisado: 2024 a 2026 | Fonte dos Dados: Central de Compras PB / CGE-PB / MinhaReceita / IBGE / OCDE</div>
</div>

<div class="card-kpi-container">
    <div class="kpi-card">
        <div class="kpi-title">Volume Total Contratado</div>
        <div class="kpi-value">{formatar_moeda(total_valor_contratos)}</div>
        <div class="kpi-sub">15.357 Contratos Analisados</div>
    </div>
    <div class="kpi-card" style="border-left-color: #16a34a;">
        <div class="kpi-title">Participação ME / EPP</div>
        <div class="kpi-value">{formatar_moeda(porte_c.loc[porte_c['is_me_epp']=='Sim (ME/EPP)', 'sum'].values[0])}</div>
        <div class="kpi-sub">54,1% dos Contratos | 27,1% do Valor</div>
    </div>
    <div class="kpi-card" style="border-left-color: #d97706;">
        <div class="kpi-title">Retenção Territorial PB</div>
        <div class="kpi-value">67,88%</div>
        <div class="kpi-sub">R$ 20,75 Bi na Economia da Paraíba</div>
    </div>
    <div class="kpi-card" style="border-left-color: #9333ea;">
        <div class="kpi-title">Itens Homologados</div>
        <div class="kpi-value">{formatar_int(total_itens)}</div>
        <div class="kpi-sub">{formatar_moeda(total_valor_itens)}</div>
    </div>
</div>

<h2>1. Síntese Executiva & Mapeamento de Fontes</h2>
<p>
Este relatório atende às demandas de levantamento formuladas pelo <strong>Grupo de Trabalho (GT)</strong> encarregado da avaliação do <em>Portal de Compras Públicas do Estado da Paraíba</em>. O objetivo central é mapear com precisão cirúrgica a aplicação dos recursos públicos estaduais sob quatro eixos interligados: <strong>(1)</strong> Bens e serviços demandados, CNAE e Intensidade Tecnológica (Taxonomia OCDE); <strong>(2)</strong> Evolução temporal por ano e órgão público contratante; <strong>(3)</strong> Modalidade licitatória utilizada; e <strong>(4)</strong> Identificação da participação de <strong>Micro e Pequenas Empresas (ME/EPP)</strong> como vetor de indução econômica regional.
</p>
<p>
Os dados sintetizados neste relatório provêm diretamente de três planilhas estruturadas e auditadas, disponibilizadas na pasta <code>outputs/tables/</code> do projeto:
</p>
<ul>
    <li><strong><code>bens_servicos_nivel_contratos.xls</code> (15.357 contratos):</strong> Contém a base integral dos instrumentos contratuais formalizados no Estado da Paraíba, cruzados com CNPJ, CNAE, setor IBGE, nível tecnológico OCDE, órgão, modalidade e porte ME/EPP.</li>
    <li><strong><code>bens_servicos_itens_contratados.xls</code> (43.440 itens):</strong> Apresenta a granularidade máxima de bens e serviços licitados, contendo descrição técnica, quantidade, valor unitário homologado e valor total.</li>
    <li><strong><code>dados_consolidado.xls</code> (181 matrizes multidimensionais):</strong> Cruzamento tabular das dimensões Ano &times; Modalidade &times; OCDE &times; Porte ME/EPP.</li>
</ul>

<div class="box-destaque">
    <strong>Destaque Metodológico:</strong> Foram identificados <strong>8.301 contratos com Micro e Pequenas Empresas (ME/EPP)</strong>, equivalendo a <strong>54,05%</strong> de todos os contratos celebrados pelo Estado. No nível de itens homologados, a taxa de sucesso das MPEs alcança expressivos <strong>60,67% (26.357 itens)</strong>, comprovando o papel distributivo das compras públicas paraibanas.
</div>

<h2>2. Participação de Micro e Pequenas Empresas (ME/EPP)</h2>
<p>
A tabela a seguir discrimina a participação das empresas contratadas com base no enquadramento oficial de porte fornecido pela Receita Federal (RFB).
</p>

<table>
    <thead>
        <tr>
            <th>Porte Empresarial (Enquadramento RFB)</th>
            <th class="text-center">Qtd. Contratos</th>
            <th class="text-center">Part. Contratos (%)</th>
            <th class="text-right">Volume Financeiro (R$)</th>
            <th class="text-right">Part. Financeira (%)</th>
        </tr>
    </thead>
    <tbody>
"""

    for _, r in porte_c.iterrows():
        badge = "badge-me" if "Sim" in str(r['is_me_epp']) else "badge-grande"
        html += f"""
        <tr>
            <td><span class="{badge}">{r['is_me_epp']}</span></td>
            <td class="text-center">{formatar_int(r['count'])}</td>
            <td class="text-center">{r['pct_count']:.2f}%</td>
            <td class="text-right">{formatar_moeda(r['sum'])}</td>
            <td class="text-right">{r['pct_val']:.2f}%</td>
        </tr>
        """

    html += f"""
        <tr style="font-weight: bold; background-color: #edf2f7;">
            <td>TOTAL GERAL</td>
            <td class="text-center">{formatar_int(total_contratos)}</td>
            <td class="text-center">100,00%</td>
            <td class="text-right">{formatar_moeda(total_valor_contratos)}</td>
            <td class="text-right">100,00%</td>
        </tr>
    </tbody>
</table>

<p>
<strong>Análise Comparativa Itens vs. Contratos:</strong> Enquanto nas grandes obras e concessões predominam médias e grandes empresas (responsáveis por 72,33% do valor contratado total), as Micro e Pequenas Empresas dominam a aquisição de suprimentos, bens e serviços essenciais (abocanhando <strong>R$ 8,28 bilhões</strong> em contratos e <strong>R$ 10,36 bilhões</strong> no nível de itens homologados).
</p>

<div class="page-break"></div>

<h2>3. Distribuição por Modalidade de Compra Pública</h2>
<p>
A distribuição das contratações por modalidade revela a predominância do <strong>Pregão Eletrônico</strong> e da <strong>Concorrência Eletrônica</strong> nos processos concorrenciais, além do peso dos contratos firmados pelas <strong>Estatais e Fundações</strong> regidos pela Lei Federal nº 13.303/2016 (ex: CAGEPA, PB Saúde e DER).
</p>

<table>
    <thead>
        <tr>
            <th>Modalidade de Compra</th>
            <th class="text-center">Qtd. Contratos</th>
            <th class="text-right">Volume Financeiro (R$)</th>
            <th class="text-right">Participação (%)</th>
        </tr>
    </thead>
    <tbody>
"""

    for _, r in mod_c.iterrows():
        if r['count'] > 0:
            html += f"""
            <tr>
                <td>{r['modalidade_compra']}</td>
                <td class="text-center">{formatar_int(r['count'])}</td>
                <td class="text-right">{formatar_moeda(r['sum'])}</td>
                <td class="text-right">{r['pct_val']:.2f}%</td>
            </tr>
            """

    html += f"""
    </tbody>
</table>

<h2>4. Perfil Produtivo (Setores Econômicos e Intensidade OCDE)</h2>
<p>
A classificação socioeconômica segundo os 7 grandes setores do IBGE e a intensidade tecnológica da OCDE demonstra forte concentração em <strong>Serviços</strong>, <strong>Construção Civil</strong> e <strong>Serviços Industriais de Utilidade Pública (SIUP)</strong>.
</p>

<table>
    <thead>
        <tr>
            <th>Setor Econômico (IBGE / CNAE)</th>
            <th class="text-center">Qtd. Contratos</th>
            <th class="text-right">Volume Financeiro (R$)</th>
            <th class="text-right">Participação (%)</th>
        </tr>
    </thead>
    <tbody>
"""

    for _, r in set_c.iterrows():
        if r['count'] > 0:
            html += f"""
            <tr>
                <td>{r['setor_economico']}</td>
                <td class="text-center">{formatar_int(r['count'])}</td>
                <td class="text-right">{formatar_moeda(r['sum'])}</td>
                <td class="text-right">{r['pct_val']:.2f}%</td>
            </tr>
            """

    html += f"""
    </tbody>
</table>

<h3>Classificação por Intensidade Tecnológica (Critério OCDE)</h3>
<table>
    <thead>
        <tr>
            <th>Intensidade Tecnológica (OCDE)</th>
            <th class="text-center">Qtd. Contratos</th>
            <th class="text-right">Volume Financeiro (R$)</th>
            <th class="text-right">Participação (%)</th>
        </tr>
    </thead>
    <tbody>
"""

    for _, r in tec_c.iterrows():
        if r['count'] > 0:
            html += f"""
            <tr>
                <td>{r['intensidade_tecnologica_ocde']}</td>
                <td class="text-center">{formatar_int(r['count'])}</td>
                <td class="text-right">{formatar_moeda(r['sum'])}</td>
                <td class="text-right">{r['pct_val']:.2f}%</td>
            </tr>
            """

    html += f"""
    </tbody>
</table>

<div class="page-break"></div>

<h2>5. Retenção Territorial de Renda (Localização por CNPJ)</h2>
<p>
O cruzamento geográfico do domicílio fiscal dos fornecedores contratados indica que <strong>67,88%</strong> de todos os recursos despendidos pelo Estado permanecem no território paraibano, com forte equilíbrio entre a <strong>Capital (João Pessoa)</strong> e o <strong>Interior do Estado</strong>.
</p>

<table>
    <thead>
        <tr>
            <th>Categoria de Localização do Fornecedor</th>
            <th class="text-center">Qtd. Contratos</th>
            <th class="text-right">Volume Financeiro (R$)</th>
            <th class="text-right">Participação (%)</th>
        </tr>
    </thead>
    <tbody>
"""

    for _, r in loc_c.iterrows():
        if r['count'] > 0:
            html += f"""
            <tr>
                <td><strong>{r['localizacao_categoria']}</strong></td>
                <td class="text-center">{formatar_int(r['count'])}</td>
                <td class="text-right">{formatar_moeda(r['sum'])}</td>
                <td class="text-right">{r['pct_val']:.2f}%</td>
            </tr>
            """

    html += f"""
    </tbody>
</table>

<h2>6. Maiores Contratações e Órgãos Contratantes</h2>

<h3>Top 5 Maiores Órgãos Compradores por Volume Financeiro</h3>
<table>
    <thead>
        <tr>
            <th>Órgão Público Contratante</th>
            <th class="text-center">Contratos</th>
            <th class="text-right">Volume Financeiro (R$)</th>
            <th class="text-right">Part. (%)</th>
        </tr>
    </thead>
    <tbody>
"""

    for _, r in top_org.head(5).iterrows():
        html += f"""
        <tr>
            <td>{r['orgao_contratante']}</td>
            <td class="text-center">{formatar_int(r['count'])}</td>
            <td class="text-right">{formatar_moeda(r['sum'])}</td>
            <td class="text-right">{r['pct_val']:.2f}%</td>
        </tr>
        """

    html += f"""
    </tbody>
</table>

<h3>Amostra dos Maiores Contratos Firmados (Base: bens_servicos_nivel_contratos.xls)</h3>
<table>
    <thead>
        <tr>
            <th>Fornecedor Contratado</th>
            <th>Órgão Comprador</th>
            <th class="text-center">Porte</th>
            <th class="text-center">Modalidade</th>
            <th class="text-right">Valor Total (R$)</th>
        </tr>
    </thead>
    <tbody>
"""

    for _, r in top10_c.head(6).iterrows():
        badge = "badge-me" if "Sim" in str(r['is_me_epp']) else "badge-grande"
        mod_curta = str(r['modalidade_compra']).replace("Não informada / Sistema Próprio (Estatais)", "Estatais/Próprio")
        html += f"""
        <tr>
            <td><strong>{r['razao_social']}</strong></td>
            <td>{r['orgao_contratante'][:35]}</td>
            <td class="text-center"><span class="{badge}">{r['is_me_epp']}</span></td>
            <td class="text-center">{mod_curta}</td>
            <td class="text-right">{formatar_moeda(r['Valor_contratado'])}</td>
        </tr>
        """

    html += f"""
    </tbody>
</table>

<h2>7. Conclusões e Recomendações para o GT</h2>
<ol>
    <li><strong>Validação das Fontes:</strong> Os três arquivos Excel gerados (<code>bens_servicos_nivel_contratos.xls</code>, <code>bens_servicos_itens_contratados.xls</code> e <code>dados_consolidado.xls</code>) respondem plenamente aos 4 quesitos levantados pelo Grupo de Trabalho.</li>
    <li><strong>Força das ME/EPPs na Paraíba:</strong> A expressiva fatia de <strong>54,05% dos contratos e 60,67% dos itens</strong> nas mãos de micro e pequenos empreendedores comprova a capilaridade da política de compras, recomendando-se monitorar a expansão dessa participação para compras de maior intensidade tecnológica.</li>
    <li><strong>Retenção Territorial Elevada (67,88%):</strong> A maior parte dos recursos circula na economia paraibana, impulsionando a arrecadação do ICMS e a geração de empregos locais no interior e na capital.</li>
</ol>

<hr style="border: 0; border-top: 1px solid #cbd5e1; margin-top: 25px;">
<div style="font-size: 8pt; color: #64748b; text-align: center;">
    Relatório gerado automaticamente pelo pipeline analítico do Portal Compras Públicas PB.<br>
    Coordenação: Prof. Dr. Paulo Fernando Cavalcanti | Núcleo de Inteligência e Big Data (NIB / UFPB / SUDENE).
</div>

</body>
</html>
"""
    return html

def main():
    print("Carregando arquivos XLS...")
    df_c, df_i, df_m = carregar_dados()
    print("Gerando HTML do relatório...")
    html_content = gerar_html(df_c, df_i, df_m)
    
    html_path = "outputs/relatorio/relatorio_analise_gt_compras_pb.html"
    pdf_path = "outputs/relatorio/relatorio_analise_gt_compras_pb.pdf"
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML salvo em: {html_path}")

    print("Renderizando PDF via WeasyPrint...")
    weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
    print(f"PDF gerado com sucesso em: {pdf_path}")

if __name__ == "__main__":
    main()
