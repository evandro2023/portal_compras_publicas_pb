import sys
import os
from pathlib import Path
import streamlit as st
import pandas as pd
import duckdb

# Garante que o diretório raiz esteja no sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from portal.utils import set_page_config, render_custom_css, render_sidebar_docs, get_db_connection
from src.etl.cnae_catalog import (
    categorizar_localizacao,
    categorizar_setor_cnae,
    categorizar_intensidade_tecnologica,
)

set_page_config(page_title="Perfil Produtivo e CNAE - Portal Compras PB")
render_custom_css()
render_sidebar_docs()

st.title("🏭 Perfil Produtivo, CNAE e Localização dos Contratados")
st.markdown("""
Esta seção analisa a distribuição das contratações públicas estaduais sob a perspectiva da **estrutura produtiva e geográfica** das empresas contratadas, conforme solicitado pelo Grupo de Trabalho (GT).

A análise categoriza o poder de compra pública por:
1. **Localização Geográfica**: Capital (João Pessoa), Interior da Paraíba, Região Nordeste e Fora do Nordeste.
2. **Intensidade Tecnológica**: Alta, Média-Alta, Média-Baixa e Baixa intensidade (Taxonomia OCDE/IBGE).
3. **Setores Econômicos**: Classificação oficial por seções CNAE (Indústria de Transformação, Extrativa, SIUP, Construção Civil, Comércio, Serviços, Agricultura/Pecuária).
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

df_base = df_todos.copy()

if selected_ano != "Todos":
    df_base = df_base[df_base["ano_contrato"] == selected_ano]

if selected_orgao != "Todos":
    df_base = df_base[df_base["nomeOrgao"] == selected_orgao]

if selected_modalidade != "Todas":
    df_base = df_base[df_base["modalidade"] == selected_modalidade]

if selected_porte != "Todos":
    df_base = df_base[df_base["is_me_epp"] == selected_porte]

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
col1.metric("Valor Total Analisado", f"R$ {total_valor:,.2f}")
col2.metric("Total de Contratos", f"{total_contratos:,}")
col3.metric("Part. Capital (PB)", f"{pct_capital:.1f}%", f"R$ {valor_capital:,.2f}")
col4.metric("Part. Interior (PB)", f"{pct_interior:.1f}%", f"R$ {valor_interior:,.2f}")
col5.metric("Part. ME/EPP", f"{pct_me_epp:.1f}%", f"R$ {valor_me_epp:,.2f}")

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
    
    df_loc["percentual"] = (df_loc["total_valor"] / total_valor * 100).round(2)
    
    col_chart, col_data = st.columns([3, 2])
    with col_chart:
        st.bar_chart(
            data=df_loc.set_index("localizacao_categoria")["total_valor"],
            height=350
        )
    
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
    
    df_tec["percentual"] = (df_tec["total_valor"] / total_valor * 100).round(2)
    
    st.bar_chart(
        data=df_tec.set_index("intensidade_tecnologica")["total_valor"],
        height=350
    )
    
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
    st.subheader("Distribuição por Setor Econômico (CNAE)")
    st.write("Volume de recursos alocados nos 7 grandes setores da economia brasileira.")
    
    df_setor = df_base.groupby("setor_economico", as_index=False).agg(
        total_valor=("valorTotal", "sum"),
        total_contratos=("valorTotal", "count")
    ).sort_values("total_valor", ascending=False)
    
    df_setor["percentual"] = (df_setor["total_valor"] / total_valor * 100).round(2)
    
    st.bar_chart(
        data=df_setor.set_index("setor_economico")["total_valor"],
        height=380
    )
    
    st.dataframe(
        df_setor.rename(columns={
            "setor_economico": "Setor Econômico",
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
        "is_me_epp", "uf", "localizacao_categoria", "setor_economico", "intensidade_tecnologica", "valorTotal"
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
            "setor_economico": "Setor",
            "intensidade_tecnologica": "Intensidade Tec.",
            "valorTotal": "Valor Total (R$)"
    })

    filtro_busca = st.text_input("🔍 Buscar por Fornecedor, CNPJ, Nº Contrato, Registro CGE, Modalidade ou Porte:", "")
    if filtro_busca:
        termo = filtro_busca.strip().lower()
        df_tabela = df_tabela[
            df_tabela["Razão Social Fornecedor"].astype(str).str.lower().str.contains(termo) |
            df_tabela["CNPJ"].astype(str).str.contains(termo) |
            df_tabela["Nº Contrato"].astype(str).str.lower().str.contains(termo) |
            df_tabela["Registro CGE"].astype(str).str.lower().str.contains(termo) |
            df_tabela["Modalidade"].astype(str).str.lower().str.contains(termo) |
            df_tabela["Porte (ME/EPP)"].astype(str).str.lower().str.contains(termo)
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
