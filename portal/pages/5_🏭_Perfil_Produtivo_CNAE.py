import streamlit as st
import pandas as pd
from utils import set_page_config, render_custom_css, render_sidebar_docs, get_db_connection

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

# --- Filtros de Dados ---
st.sidebar.subheader("🔍 Filtros de Análise")

# Carrega os anos disponíveis
df_anos = conn.execute("""
    SELECT DISTINCT ano_contrato 
    FROM vw_analise_compras_cnae_localizacao 
    WHERE ano_contrato IS NOT NULL 
    ORDER BY ano_contrato DESC
""").df()

anos_list = ["Todos"] + [int(a) for a in df_anos["ano_contrato"].dropna().tolist()]
selected_ano = st.sidebar.selectbox("Ano do Contrato:", anos_list)

# Query base filtrada
where_clause = "WHERE 1=1"
if selected_ano != "Todos":
    where_clause += f" AND ano_contrato = {selected_ano}"

df_base = conn.execute(f"""
    SELECT * 
    FROM vw_analise_compras_cnae_localizacao 
    {where_clause}
""").df()

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

valor_alta_tec = df_base[df_base["intensidade_tecnologica"].str.contains("Alta", na=False)]["valorTotal"].sum()
pct_alta_tec = (valor_alta_tec / total_valor * 100) if total_valor > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Valor Total Analisado", f"R$ {total_valor:,.2f}")
col2.metric("Total de Contratos", f"{total_contratos:,}")
col3.metric("Participação Capital (PB)", f"{pct_capital:.1f}%", f"R$ {valor_capital:,.2f}")
col4.metric("Participação Interior (PB)", f"{pct_interior:.1f}%", f"R$ {valor_interior:,.2f}")

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
    
    st.dataframe(
        df_base[[
            "numeroContrato", "nomeOrgao", "razao_social", "cnpj_clean", 
            "uf", "localizacao_categoria", "setor_economico", "intensidade_tecnologica", "valorTotal"
        ]].rename(columns={
            "numeroContrato": "Nº Contrato",
            "nomeOrgao": "Órgão Contratante",
            "razao_social": "Razão Social Fornecedor",
            "cnpj_clean": "CNPJ",
            "uf": "UF",
            "localizacao_categoria": "Localização",
            "setor_economico": "Setor",
            "intensidade_tecnologica": "Intensidade Tec.",
            "valorTotal": "Valor Total (R$)"
        }),
        column_config={
            "Valor Total (R$)": st.column_config.NumberColumn(format="R$ %,.2f")
        },
        hide_index=True
    )
