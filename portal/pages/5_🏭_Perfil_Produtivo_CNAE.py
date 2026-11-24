import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px
import sys
import os

import sys
import os
import importlib

# Ajusta o path para importar utils da raiz do portal garantindo precedência absoluta
portal_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if portal_dir not in sys.path:
    sys.path.insert(0, portal_dir)

# Força reload do módulo utils para evitar cache obsoleto em containers persistentes (Streamlit Cloud)
try:
    import utils
    importlib.reload(utils)
    from utils import (
        set_page_config,
        render_custom_css,
        render_sidebar_docs,
        get_db_connection,
        categorizar_localizacao,
        categorizar_setor_cnae,
        categorizar_intensidade_tecnologica,
        categorizar_ibge_pim_estrito,
        categorizar_ibge_cadeia_ampla,
        categorizar_grande_setor,
        aplicar_estilo_grafico,
    )
except Exception:
    import utils
    from utils import (
        set_page_config,
        render_custom_css,
        render_sidebar_docs,
        get_db_connection,
    )
    def categorizar_ibge_pim_estrito(c): return getattr(utils, 'categorizar_ibge_pim_estrito', lambda x: None)(c)
    def categorizar_ibge_cadeia_ampla(c): return getattr(utils, 'categorizar_ibge_cadeia_ampla', lambda x: 'Não Classificado')(c)
    def categorizar_grande_setor(c): return getattr(utils, 'categorizar_grande_setor', lambda x: 'Não Classificado')(c)
    def aplicar_estilo_grafico(f, altura=None): return getattr(utils, 'aplicar_estilo_grafico', lambda fig, a=None: fig)(f, altura)

set_page_config(page_title="Perfil Produtivo e CNAE - Portal Compras PB")
render_custom_css()
render_sidebar_docs()

st.title("🏭 Perfil Produtivo, CNAE e Localização dos Contratados")
st.markdown("""
Esta seção analisa a distribuição das contratações públicas estaduais sob a perspectiva da **estrutura produtiva e geográfica** das empresas contratadas, conforme solicitado pelo Grupo de Trabalho (GT).

A análise categoriza o poder de compra pública por:
1. **Localização Geográfica**: Capital (João Pessoa), Interior da Paraíba, Região Nordeste e Fora do Nordeste.
2. **Intensidade Tecnológica**: Alta, Média-Alta, Média-Baixa e Baixa intensidade (Taxonomia OCDE/IBGE).
3. **Grandes Setores e Categorias Econômicas (IBGE / CGCE)**: Bens de Capital, Bens Intermediários, Bens de Consumo Duráveis, Bens de Consumo Semiduráveis/Não Duráveis, Construção Civil, SIUP, Serviços e Agropecuária.
4. **Setores Econômicos Tradicionais**: Classificação oficial por seções CNAE.
""")

# --- Card Informativo sobre Sergipe ---
st.info("""
📌 **Nota Metodológica sobre Sergipe (SE):**  
Nesta etapa, o acervo referente a Sergipe no sistema encontra-se focado no mapeamento legislativo e regulatório comparado. A análise quantitativa de microdados por CNPJ, CNAE e localização geográfica detalhada a seguir é aplicada à base de contratos da Paraíba (PB).
""")

conn = get_db_connection()


def obter_dataframe_analitico(conn):
    """Garante o carregamento dos dados com resiliência a ausência de tabelas pré-computadas."""
    tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]

    # 1. Consulta integrada com contratos, licitações (modalidade) e fornecedores (porte ME/EPP e CNAE)
    if "contratos" in tables and "dim_fornecedores_cnae" in tables:
        try:
            return conn.execute("""
                WITH licitacoes_dedup AS (
                    SELECT 
                        numeroProcesso,
                        FIRST(modalidade) AS modalidade
                    FROM contratacoes
                    WHERE numeroProcesso IS NOT NULL
                    GROUP BY numeroProcesso
                )
                SELECT 
                    c.registroCge,
                    c.numeroContrato,
                    c.nomeOrgao,
                    c.dataAssinatura,
                    COALESCE(c.ano_referencia, YEAR(TRY_CAST(c.dataAssinatura AS DATE))) as ano_contrato,
                    COALESCE(l.modalidade, 'Não informada / Sistema Próprio (Estatais)') as modalidade,
                    c.valorTotal,
                    c.contratado as nome_contratado_contrato,
                    REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') as cnpj_clean,
                    f.razao_social,
                    f.uf,
                    f.municipio as municipio_fornecedor,
                    COALESCE(f.localizacao_categoria, 'Não Identificado') as localizacao_categoria,
                    COALESCE(f.porte, 'N/D') as porte_receita,
                    CASE 
                        WHEN f.porte IN ('MICRO EMPRESA', 'EMPRESA DE PEQUENO PORTE') THEN 'Sim (ME/EPP)'
                        WHEN f.porte = 'DEMAIS' THEN 'Não (Média/Grande)'
                        ELSE 'Não Identificado / PF'
                    END as is_me_epp,
                    COALESCE(f.cnae_fiscal, 0) as cnae_fiscal,
                    COALESCE(f.cnae_descricao, 'Não Informado') as cnae_descricao,
                    COALESCE(f.setor_economico, 'Não Classificado') as setor_economico,
                    COALESCE(f.intensidade_tecnologica, 'Não Classificado') as intensidade_tecnologica
                FROM contratos c
                LEFT JOIN licitacoes_dedup l 
                    ON c.numeroProcessoLicitacao = l.numeroProcesso
                LEFT JOIN dim_fornecedores_cnae f 
                    ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = LPAD(CAST(CAST(f.cnpj AS BIGINT) AS VARCHAR), 14, '0')
            """).df()
        except Exception:
            pass

    # 2. Tenta consulta direta da view pré-computada se existir
    if "vw_analise_compras_cnae_localizacao" in tables:
        try:
            return conn.execute("SELECT * FROM vw_analise_compras_cnae_localizacao").df()
        except Exception:
            pass

    return pd.DataFrame()


df_todos = obter_dataframe_analitico(conn)


def deduplicar_contratos(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém um único registro por contrato (registroCge).

    A base bruta contém snapshots repetidos do mesmo contrato (ingestões
    sucessivas). Para não inflar somas, mantém-se a versão de maior valorTotal
    (a mais atualizada, pois aditivos/apostilas só acrescem ao valor).
    """
    if df.empty or "registroCge" not in df.columns:
        return df
    # Contratos sem registroCge (origem PNCP) não podem ser deduplicados por essa
    # chave (colapsariam em um só); a deduplicação deles é feita no ETL.
    com_id = df[df["registroCge"].notna()]
    sem_id = df[df["registroCge"].isna()]
    com_id = com_id.sort_values("valorTotal", ascending=False, na_position="last").drop_duplicates(
        subset="registroCge", keep="first"
    )
    return pd.concat([com_id, sem_id]).sort_index().reset_index(drop=True)


_n_bruto = len(df_todos)
df_todos = deduplicar_contratos(df_todos)
_n_duplicados = _n_bruto - len(df_todos)

if not df_todos.empty and "cnae_fiscal" in df_todos.columns:
    df_todos["categoria_ibge_estrita"] = df_todos["cnae_fiscal"].apply(categorizar_ibge_pim_estrito)
    df_todos["categoria_ibge_ampla"] = df_todos["cnae_fiscal"].apply(categorizar_ibge_cadeia_ampla)
    df_todos["grande_setor"] = df_todos["categoria_ibge_ampla"]

if df_todos.empty:
    st.warning("⚠️ Não foi possível carregar os microdados de contratos no momento.")
    st.stop()

# --- Filtros de Dados ---
st.sidebar.subheader("🔍 Filtros de Análise")

anos_list = ["Todos"] + sorted(
    [int(a) for a in df_todos["ano_contrato"].dropna().unique() if str(a).isdigit()],
    reverse=True,
)
selected_ano = st.sidebar.selectbox("Ano do Contrato:", anos_list)

orgaos_list = ["Todos"] + sorted(df_todos["nomeOrgao"].dropna().unique().tolist())
selected_orgao = st.sidebar.selectbox("Órgão Contratante:", orgaos_list)

modalidades_list = ["Todas"] + sorted([str(m) for m in df_todos["modalidade"].dropna().unique() if str(m).strip()])
selected_modalidade = st.sidebar.selectbox("Modalidade de Compra:", modalidades_list)

portes_list = ["Todos", "Sim (ME/EPP)", "Não (Média/Grande)", "Não Identificado / PF"]
selected_porte = st.sidebar.selectbox("Porte (ME/EPP):", portes_list)

grandes_setores_list = ["Todos"] + sorted([str(s) for s in df_todos["grande_setor"].dropna().unique() if str(s).strip()])
selected_grande_setor = st.sidebar.selectbox("Grande Área / Setor (IBGE):", grandes_setores_list)

df_base = df_todos.copy()

if selected_ano != "Todos":
    df_base = df_base[df_base["ano_contrato"] == selected_ano]

if selected_orgao != "Todos":
    df_base = df_base[df_base["nomeOrgao"] == selected_orgao]

if selected_modalidade != "Todas":
    df_base = df_base[df_base["modalidade"] == selected_modalidade]

if selected_porte != "Todos":
    df_base = df_base[df_base["is_me_epp"] == selected_porte]

if selected_grande_setor != "Todos":
    df_base = df_base[df_base["grande_setor"] == selected_grande_setor]

if df_base.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

# --- KPIs Principais ---
total_valor = df_base["valorTotal"].sum()
total_contratos = len(df_base)

valor_capital = df_base[df_base["localizacao_categoria"] == "Capital (PB)"]["valorTotal"].sum()
valor_interior = df_base[df_base["localizacao_categoria"] == "Interior (PB)"]["valorTotal"].sum()

pct_capital = (valor_capital / total_valor * 100) if total_valor > 0 else 0
pct_interior = (valor_interior / total_valor * 100) if total_valor > 0 else 0

valor_me_epp = df_base[df_base["is_me_epp"] == "Sim (ME/EPP)"]["valorTotal"].sum()
pct_me_epp = (valor_me_epp / total_valor * 100) if total_valor > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Valor Total Analisado", f"R$ {total_valor:,.2f}", border=True)
col2.metric("Total de Contratos", f"{total_contratos:,}", border=True)
col3.metric("Part. Capital (PB)", f"{pct_capital:.1f}%", f"R$ {valor_capital:,.2f}", border=True)
col4.metric("Part. Interior (PB)", f"{pct_interior:.1f}%", f"R$ {valor_interior:,.2f}", border=True)
col5.metric("Part. ME/EPP", f"{pct_me_epp:.1f}%", f"R$ {valor_me_epp:,.2f}", border=True)

st.markdown("---")

# --- Abas de Detalhamento ---
tab_loc, tab_tec, tab_setor, tab_tabela = st.tabs([
    "📍 a) Localização dos Contratados", 
    "🔬 b) Intensidade Tecnológica", 
    "🏭 c) Setores Econômicos",
    "📄 Dados Detalhados"
])

# --- ABA 1: LOCALIZAÇÃO ---
with tab_loc:
    st.subheader("Localização dos Fornecedores Contratados")
    st.write("Distribuição do valor contratado segundo o domicílio fiscal da empresa (Capital, Interior, Nordeste e Outras Regiões).")
    
    df_loc = df_base.groupby("localizacao_categoria", as_index=False).agg(
        total_valor=("valorTotal", "sum"),
        total_contratos=("valorTotal", "count")
    ).sort_values("total_valor", ascending=False)
    
    df_loc["percentual"] = (df_loc["total_valor"] / total_valor * 100).round(2) if total_valor > 0 else 0
    
    col_chart, col_data = st.columns([3, 2])
    with col_chart:
        fig_loc = px.bar(
            df_loc,
            x="total_valor",
            y="localizacao_categoria",
            orientation="h",
            text="total_valor",
            color="localizacao_categoria",
            labels={"total_valor": "<b>Volume Contratado (R$)</b>", "localizacao_categoria": "<b>Localização</b>"},
            title="<b>Volume Contratado por Localização do Fornecedor</b>",
            color_discrete_map={
                "Capital (PB)": "#0f52ba",
                "Interior (PB)": "#16a34a",
                "Nordeste (Demais UFs)": "#d97706",
                "Fora do Nordeste": "#dc2626",
                "Não Identificado": "#94a3b8"
            }
        )
        fig_loc.update_traces(
            texttemplate="<b>R$ %{text:,.2s}</b>",
            textposition="outside",
            showlegend=False
        )
        fig_loc.update_layout(yaxis={"categoryorder": "total ascending", "title": ""})
        aplicar_estilo_grafico(fig_loc, altura=360)
        st.plotly_chart(fig_loc, width="stretch")
    
    with col_data:
        st.dataframe(
            df_loc.rename(columns={
                "localizacao_categoria": "Categoria Geográfica",
                "total_valor": "Valor Total (R$)",
                "total_contratos": "Contratos",
                "percentual": "Part. (%)"
            }),
            column_config={
                "Valor Total (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Part. (%)": st.column_config.NumberColumn(format="%.2f %%")
            },
            hide_index=True
        )

# --- ABA 2: INTENSIDADE TECNOLÓGICA ---
with tab_tec:
    st.subheader("Classificação por Intensidade Tecnológica")
    st.write("Agrupamento das empresas contratadas com base na taxonomia OCDE/IBGE de intensidade de P&D e inovação.")
    
    df_tec = df_base.groupby("intensidade_tecnologica", as_index=False).agg(
        total_valor=("valorTotal", "sum"),
        total_contratos=("valorTotal", "count")
    ).sort_values("total_valor", ascending=False)
    
    df_tec["percentual"] = (df_tec["total_valor"] / total_valor * 100).round(2) if total_valor > 0 else 0
    
    col_tec_chart, col_tec_data = st.columns([3, 2])
    with col_tec_chart:
        fig_tec = px.bar(
            df_tec,
            x="total_valor",
            y="intensidade_tecnologica",
            orientation="h",
            text="total_valor",
            color="intensidade_tecnologica",
            labels={"total_valor": "<b>Volume Contratado (R$)</b>", "intensidade_tecnologica": "<b>Intensidade Tecnológica</b>"},
            title="<b>Volume por Intensidade Tecnológica (OCDE/IBGE)</b>",
            color_discrete_map={
                "Alta Intensidade Tecnológica": "#7c3aed",
                "Média-Alta Intensidade Tecnológica": "#0284c7",
                "Média-Baixa Intensidade Tecnológica": "#0f766e",
                "Baixa Intensidade Tecnológica": "#16a34a",
                "Alta Intensidade Tecnológica (Serviços KIS)": "#d97706",
                "Serviços e Outros (Não-Industrial)": "#64748b",
                "Não Classificado": "#94a3b8"
            }
        )
        fig_tec.update_traces(
            texttemplate="<b>R$ %{text:,.2s}</b>",
            textposition="outside",
            showlegend=False
        )
        fig_tec.update_layout(yaxis={"categoryorder": "total ascending", "title": ""})
        aplicar_estilo_grafico(fig_tec, altura=380)
        st.plotly_chart(fig_tec, width="stretch")
    
    with col_tec_data:
        st.dataframe(
            df_tec.rename(columns={
                "intensidade_tecnologica": "Intensidade Tecnológica",
                "total_valor": "Valor Total (R$)",
                "total_contratos": "Contratos",
                "percentual": "Part. (%)"
            }),
            column_config={
                "Valor Total (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Part. (%)": st.column_config.NumberColumn(format="%.2f %%")
            },
            hide_index=True
        )

# --- ABA 3: SETOR ECONÔMICO ---
with tab_setor:
    st.subheader("Distribuição por Grandes Categorias Econômicas (IBGE / PIM-PF)")
    st.write(
        "Mapeamento do volume financeiro sob as **Grandes Categorias Econômicas do IBGE** "
        "(Classificação por Grandes Categorias Econômicas - CGCE / Pesquisa Industrial Mensal - PIM-PF, Tabela 8889 SIDRA). "
        "Permite distinguir com precisão entre o que é contratado diretamente de **indústrias fabricantes** versus a **cadeia ampla de bens físicos** (incluindo comércio atacadista/distribuidor)."
    )

    modo_analise = st.radio(
        "🎯 **Selecione a Abordagem Metodológica (Conforme Relatório Técnico GT):**",
        [
            "🏭 Abordagem 1: Indústria Fabricante Estrita (PIM-PF / Divisões 05 a 33)",
            "📦 Abordagem 2: Cadeia Ampla de Aquisição de Bens (Indústria + Comércio Distribuidor)"
        ],
        horizontal=True,
        help="A Abordagem 1 capta apenas indústrias fabris estritas. A Abordagem 2 inclui o comércio distribuidor que revende bens produzidos pela indústria (ex: distribuidoras farmacêuticas e de veículos/TI)."
    )

    cores_pim = {
        "Bens de Capital": "#1d4ed8",
        "Bens Intermediários": "#0284c7",
        "Bens de Consumo Duráveis": "#7c3aed",
        "Bens de Consumo Semiduráveis e Não Duráveis": "#16a34a",
        "Construção Civil (Infraestrutura/FBCF)": "#d97706",
        "Serviços Industriais de Utilidade Pública (SIUP)": "#0f766e",
        "Serviços Gerais": "#64748b",
        "Agropecuária": "#854d0e",
        "Demais Setores": "#94a3b8",
        "Não Classificado": "#cbd5e1",
    }

    if "Abordagem 1" in modo_analise:
        st.markdown("#### 🏭 Abordagem 1: Indústria Fabricante Estrita (PIM-PF)")
        st.caption(
            "Mapeamento restrito aos fornecedores cuja atividade econômica principal pertence às "
            "**Divisões 05 a 33 da CNAE** (Indústrias Extrativas e de Transformação), excluindo intermediários comerciais."
        )

        df_ab1 = df_base[df_base["categoria_ibge_estrita"].notna()].copy()
        total_ab1_valor = df_ab1["valorTotal"].sum()
        total_ab1_qtd = len(df_ab1)
        total_ab1_cge = df_ab1["registroCge"].nunique()
        total_ab1_pncp = total_ab1_qtd - total_ab1_cge

        # Total de bens na abordagem 2 para calcular a participação
        df_bens_amplo = df_base[df_base["categoria_ibge_ampla"].isin([
            "Bens de Capital", "Bens Intermediários", "Bens de Consumo Duráveis", "Bens de Consumo Semiduráveis e Não Duráveis"
        ])]
        total_bens_amplo_valor = df_bens_amplo["valorTotal"].sum()

        pct_sobre_bens = (total_ab1_valor / total_bens_amplo_valor * 100) if total_bens_amplo_valor > 0 else 0
        pct_sobre_global = (total_ab1_valor / total_valor * 100) if total_valor > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Volume Direto Fabril", f"R$ {total_ab1_valor:,.2f}", border=True)
        k2.metric(
            "Contratos com Fábricas",
            f"{total_ab1_cge:,}",
            f"{total_ab1_qtd:,} total c/ PNCP",
            help=f"Total de {total_ab1_cge:,} contratos com registro estadual CGE (conforme tabela do Relatório GT 02) ou {total_ab1_qtd:,} considerando a base integral com registros PNCP.",
            border=True
        )
        k3.metric("Part. sobre Bens Físicos", f"{pct_sobre_bens:.1f}%", border=True)
        k4.metric("Part. no Total Global", f"{pct_sobre_global:.2f}%", border=True)

        if df_ab1.empty:
            st.info("Nenhum contrato com indústrias fabricantes encontrado para os filtros selecionados.")
        else:
            df_pim_grp = df_ab1.groupby("categoria_ibge_estrita", as_index=False).agg(
                total_valor=("valorTotal", "sum"),
                total_contratos_cge=("registroCge", "nunique"),
                total_contratos=("valorTotal", "count")
            ).sort_values("total_valor", ascending=False)
            df_pim_grp["percentual"] = (df_pim_grp["total_valor"] / total_ab1_valor * 100).round(2)
            df_pim_grp["ticket_medio"] = (df_pim_grp["total_valor"] / df_pim_grp["total_contratos"]).round(2)

            c_chart, c_tbl = st.columns([3, 2])
            with c_chart:
                fig_pim = px.bar(
                    df_pim_grp,
                    x="total_valor",
                    y="categoria_ibge_estrita",
                    orientation="h",
                    text="total_valor",
                    color="categoria_ibge_estrita",
                    labels={"total_valor": "<b>Volume Contratado (R$)</b>", "categoria_ibge_estrita": "<b>Categoria PIM-PF</b>"},
                    title=f"<b>Indústria Fabricante por Categoria PIM-PF — {selected_ano if selected_ano != 'Todos' else 'Consolidado'}</b>",
                    color_discrete_map=cores_pim
                )
                fig_pim.update_traces(
                    texttemplate="<b>R$ %{text:,.2s}</b>",
                    textposition="outside",
                    showlegend=False
                )
                fig_pim.update_layout(
                    yaxis={"categoryorder": "total ascending", "title": ""}
                )
                aplicar_estilo_grafico(fig_pim, altura=370)
                st.plotly_chart(fig_pim, width="stretch")

            with c_tbl:
                st.markdown("##### 📋 Composição da Indústria Fabricante")
                st.dataframe(
                    df_pim_grp.rename(columns={
                        "categoria_ibge_estrita": "Categoria PIM-PF",
                        "total_valor": "Valor Total (R$)",
                        "total_contratos_cge": "Contratos (CGE)",
                        "total_contratos": "Contratos (Total)",
                        "percentual": "Part. Indústria (%)",
                        "ticket_medio": "Ticket Médio (R$)"
                    }),
                    column_config={
                        "Valor Total (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                        "Ticket Médio (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                        "Part. Indústria (%)": st.column_config.NumberColumn(format="%.2f %%")
                    },
                    hide_index=True,
                    width="stretch"
                )

            st.info(
                "💡 **Destaque Metodológico do GT:** Na contratação direta com fábricas (Abordagem 1), "
                "os setores de **Bens de Capital** e **Bens Intermediários** concentram mais de 65% das contratações. "
                "Medicamentos e itens hospitalares aparecem com volume reduzido porque a administração pública adquire "
                "quase a totalidade desses insumos via empresas **distribuidoras e atacadistas** (captadas na Abordagem 2)."
            )

    else:
        st.markdown("#### 📦 Abordagem 2: Cadeia Ampla de Aquisição de Bens (Indústria + Comércio Distribuidor)")
        st.caption(
            "Mapeamento integral do fornecimento de bens físicos ao Estado, englobando tanto indústrias fabris "
            "quanto **distribuidoras e comércio atacadista/varejista** (CNAEs 45 a 47) e os macrosetores de infraestrutura e serviços."
        )

        categorias_bens = [
            "Bens de Capital", "Bens Intermediários", "Bens de Consumo Duráveis", "Bens de Consumo Semiduráveis e Não Duráveis"
        ]
        df_bens = df_base[df_base["categoria_ibge_ampla"].isin(categorias_bens)].copy()
        total_bens = df_bens["valorTotal"].sum()
        qtd_bens = len(df_bens)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total da Cadeia de Bens", f"R$ {total_bens:,.2f}", border=True)
        k2.metric("Contratos de Bens Físicos", f"{qtd_bens:,}", border=True)
        k3.metric("Part. no Orçamento Global", f"{(total_bens / total_valor * 100):.1f}%" if total_valor > 0 else "0.0%", border=True)
        k4.metric("Volume Global de Contratos", f"R$ {total_valor:,.2f}", border=True)

        visao_ampla = st.radio(
            "**Nível de Detalhamento:**",
            options=["📦 Apenas as 4 Categorias de Bens (PIM-PF)", "🌐 Visão Sistêmica Completa (Bens + Infraestrutura + Serviços)"],
            horizontal=True
        )

        if visao_ampla == "📦 Apenas as 4 Categorias de Bens (PIM-PF)":
            df_amplo_grp = df_bens.groupby("categoria_ibge_ampla", as_index=False).agg(
                total_valor=("valorTotal", "sum"),
                total_contratos=("valorTotal", "count")
            ).sort_values("total_valor", ascending=False)
            df_amplo_grp["percentual"] = (df_amplo_grp["total_valor"] / total_bens * 100).round(2) if total_bens > 0 else 0
            df_amplo_grp["ticket_medio"] = (df_amplo_grp["total_valor"] / df_amplo_grp["total_contratos"]).round(2) if len(df_amplo_grp) > 0 else 0
            titulo_grafico = f"<b>Cadeia Ampla de Bens (PIM-PF + Atacado) — {selected_ano if selected_ano != 'Todos' else 'Consolidado'}</b>"
        else:
            df_amplo_grp = df_base.groupby("categoria_ibge_ampla", as_index=False).agg(
                total_valor=("valorTotal", "sum"),
                total_contratos=("valorTotal", "count")
            ).sort_values("total_valor", ascending=False)
            df_amplo_grp["percentual"] = (df_amplo_grp["total_valor"] / total_valor * 100).round(2) if total_valor > 0 else 0
            df_amplo_grp["ticket_medio"] = (df_amplo_grp["total_valor"] / df_amplo_grp["total_contratos"]).round(2) if len(df_amplo_grp) > 0 else 0
            titulo_grafico = f"<b>Visão Sistêmica Completa por Macrosetores — {selected_ano if selected_ano != 'Todos' else 'Consolidado'}</b>"

        c_chart2, c_tbl2 = st.columns([3, 2])
        with c_chart2:
            fig_ampla = px.bar(
                df_amplo_grp,
                x="total_valor",
                y="categoria_ibge_ampla",
                orientation="h",
                text="total_valor",
                color="categoria_ibge_ampla",
                labels={"total_valor": "<b>Volume Contratado (R$)</b>", "categoria_ibge_ampla": "<b>Categoria Econômica</b>"},
                title=titulo_grafico,
                color_discrete_map=cores_pim
            )
            fig_ampla.update_traces(
                texttemplate="<b>R$ %{text:,.2s}</b>",
                textposition="outside",
                showlegend=False
            )
            fig_ampla.update_layout(
                yaxis={"categoryorder": "total ascending", "title": ""}
            )
            aplicar_estilo_grafico(fig_ampla, altura=430)
            st.plotly_chart(fig_ampla, width="stretch")

        with c_tbl2:
            st.markdown("##### 📋 Detalhamento da Cadeia Ampla")
            st.dataframe(
                df_amplo_grp.rename(columns={
                    "categoria_ibge_ampla": "Categoria Econômica",
                    "total_valor": "Valor Total (R$)",
                    "total_contratos": "Contratos",
                    "percentual": "Part. (%)",
                    "ticket_medio": "Ticket Médio (R$)"
                }),
                column_config={
                    "Valor Total (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Ticket Médio (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Part. (%)": st.column_config.NumberColumn(format="%.2f %%")
                },
                hide_index=True,
                width="stretch"
            )

        st.success(
            "💡 **Efeito Multiplicador do Atacado e Distribuição:** Na Abordagem 2, os **Bens Semiduráveis e Não Duráveis** "
            "saltam para a liderança absoluta com mais de R$ 599 milhões em 2026. "
            "Isso demonstra o papel crucial das distribuidoras de medicamentos, insumos hospitalares e alimentos na cadeia de compras públicas."
        )

    st.markdown("---")
    st.subheader("Distribuição Tradicional por Seção CNAE (7 Setores da Economia)")
    st.write("Volume de recursos alocados nas seções primárias da Classificação Nacional de Atividades Econômicas.")

    df_setor = df_base.groupby("setor_economico", as_index=False).agg(
        total_valor=("valorTotal", "sum"),
        total_contratos=("valorTotal", "count")
    ).sort_values("total_valor", ascending=False)

    df_setor["percentual"] = (df_setor["total_valor"] / total_valor * 100).round(2) if total_valor > 0 else 0

    col_set_chart, col_set_data = st.columns([3, 2])
    with col_set_chart:
        fig_setor = px.bar(
            df_setor,
            x="total_valor",
            y="setor_economico",
            orientation="h",
            text="total_valor",
            color="setor_economico",
            labels={"total_valor": "<b>Volume Contratado (R$)</b>", "setor_economico": "<b>Setor Tradicional CNAE</b>"},
            title="<b>Volume por Seção Primária da CNAE</b>",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_setor.update_traces(
            texttemplate="<b>R$ %{text:,.2s}</b>",
            textposition="outside",
            showlegend=False
        )
        fig_setor.update_layout(yaxis={"categoryorder": "total ascending", "title": ""})
        aplicar_estilo_grafico(fig_setor, altura=380)
        st.plotly_chart(fig_setor, width="stretch")
    with col_set_data:
        st.dataframe(
            df_setor.rename(columns={
                "setor_economico": "Setor Tradicional CNAE",
                "total_valor": "Valor Total (R$)",
                "total_contratos": "Contratos",
                "percentual": "Part. (%)"
            }),
            column_config={
                "Valor Total (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Part. (%)": st.column_config.NumberColumn(format="%.2f %%")
            },
            hide_index=True,
            width="stretch"
        )

# --- ABA 4: DADOS DETALHADOS ---
with tab_tabela:
    st.subheader("Microdados de Contratos com Enriquecimento Produtivo")
    st.write("Visualização tabular completa dos contratos cruzados com a receita federal e CNAE.")
    st.caption(
        f"Uma linha por contrato (`registroCge` único). {_n_duplicados:,} registros duplicados "
        f"da base bruta foram removidos; a soma da coluna Valor Total confere com o KPI "
        f"**R$ {total_valor:,.2f}** ({total_contratos:,} contratos)."
    )

    df_tabela = df_base[[
        "registroCge", "numeroContrato", "nomeOrgao", "modalidade", "razao_social", "cnpj_clean",
        "is_me_epp", "uf", "localizacao_categoria", "categoria_ibge_estrita", "categoria_ibge_ampla", "setor_economico", "intensidade_tecnologica", "valorTotal"
    ]].sort_values("valorTotal", ascending=False).rename(columns={
            "registroCge": "Registro CGE",
            "numeroContrato": "Nº Contrato",
            "nomeOrgao": "Órgão Contratante",
            "modalidade": "Modalidade",
            "razao_social": "Razão Social Fornecedor",
            "cnpj_clean": "CNPJ",
            "is_me_epp": "Porte (ME/EPP)",
            "uf": "UF",
            "localizacao_categoria": "Localização",
            "categoria_ibge_estrita": "Categoria PIM (Fabricante)",
            "categoria_ibge_ampla": "Categoria PIM (Cadeia Ampla)",
            "setor_economico": "Setor CNAE",
            "intensidade_tecnologica": "Intensidade Tec.",
            "valorTotal": "Valor Total (R$)"
    })

    filtro_busca = st.text_input("🔍 Buscar por Fornecedor, CNPJ, Nº Contrato, Registro CGE, Modalidade, Porte ou Categoria Econômica:", "")
    if filtro_busca:
        termo = filtro_busca.strip().lower()
        df_tabela = df_tabela[
            df_tabela["Razão Social Fornecedor"].astype(str).str.lower().str.contains(termo) |
            df_tabela["CNPJ"].astype(str).str.contains(termo) |
            df_tabela["Nº Contrato"].astype(str).str.lower().str.contains(termo) |
            df_tabela["Registro CGE"].astype(str).str.lower().str.contains(termo) |
            df_tabela["Modalidade"].astype(str).str.lower().str.contains(termo) |
            df_tabela["Porte (ME/EPP)"].astype(str).str.lower().str.contains(termo) |
            df_tabela["Categoria PIM (Fabricante)"].astype(str).str.lower().str.contains(termo) |
            df_tabela["Categoria PIM (Cadeia Ampla)"].astype(str).str.lower().str.contains(termo)
        ]

    st.dataframe(
        df_tabela,
        column_config={
            "Valor Total (R$)": st.column_config.NumberColumn(format="R$ %,.2f")
        },
        width="stretch",
        hide_index=True
    )
    
    csv_filename = "contratos_perfil_produtivo.csv"
    if selected_orgao != "Todos":
        sufixo = "".join(c for c in selected_orgao[:20] if c.isalnum() or c == "_").lower()
        csv_filename = f"contratos_{sufixo}_{selected_ano}.csv"

    st.download_button(
        "⬇️ Baixar CSV",
        df_tabela.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name=csv_filename,
        mime="text/csv",
    )
