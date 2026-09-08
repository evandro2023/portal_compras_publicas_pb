import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Ajusta o path para importar utils da raiz do portal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import set_page_config, get_db_connection, render_sidebar_docs

# Configuração da página
set_page_config("Módulo de Dados Econômicos & CAGED")
render_sidebar_docs()

st.title("📈 Módulo de Dados Econômicos (CAGED Paraíba)")
st.markdown("""
Análise dos microdados de movimentação de emprego formal (**Novo CAGED**) na Paraíba,
consolidado por município e agrupado por **Classe CNAE** e **Seção Econômica**.
""")

# --- FILTROS LATERAIS ---

st.sidebar.header("Filtros Analíticos")

# Filtro de Nível CNAE
nivel_selecionado = st.sidebar.selectbox(
    "Nível de Agregação CNAE",
    options=["classe", "secao", "subclasse"],
    format_func=lambda x: {"classe": "Classe CNAE (4 dígitos - Recomendado)", "secao": "Seção Econômica", "subclasse": "Subclasse CNAE"}.get(x, x)
)

# Filtro de Ano
anos_disponiveis = [2025, 2026]
ano_selecionado = st.sidebar.selectbox("Ano de Referência", anos_disponiveis, index=0)

# Consulta SQL ao DuckDB
table_name = f"caged_pb_{nivel_selecionado}_{ano_selecionado}"

@st.cache_data(ttl=300)
def load_caged_data(tbl_name: str, nivel: str):
    conn = get_db_connection()
    tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parquet_path = os.path.join(base_dir, "data", "processed", "caged", f"{tbl_name}.parquet")

    # Se a tabela não existir no banco DuckDB em memória/disco, cria dinamicamente a partir do Parquet
    if tbl_name not in tables:
        if os.path.exists(parquet_path):
            conn.execute(f"CREATE TABLE IF NOT EXISTS {tbl_name} AS SELECT * FROM read_parquet('{parquet_path}')")
            tables.append(tbl_name)
        else:
            conn.close()
            return None

    # Se a tabela ainda não tiver a coluna nome_classe e for nível classe, realiza JOIN leve com a tabela auxiliar
    columns = [c[0] for c in conn.execute(f"DESCRIBE {tbl_name}").fetchall()]
    
    if nivel == "classe" and "nome_classe" not in columns:
        secao_classe_csv = os.path.join(base_dir, "src", "caged", "secao_classe.csv")
        if "caged_secao_classe" not in tables and os.path.exists(secao_classe_csv):
            conn.execute(f"CREATE TABLE IF NOT EXISTS caged_secao_classe AS SELECT LOWER(TRIM(secao)) as secao, TRIM(classe) as classe, TRIM(nome) as nome FROM read_csv('{secao_classe_csv}', sep=';', header=True)")
            tables.append("caged_secao_classe")

        if "caged_secao_classe" in tables:
            query = f"""
                SELECT 
                    c.*,
                    COALESCE(s.nome, 'Classe ' || CAST(TRY_CAST(c."Classe" AS BIGINT) AS VARCHAR)) AS nome_classe,
                    s.secao AS codigo_secao
                FROM {tbl_name} c
                LEFT JOIN caged_secao_classe s ON CAST(TRY_CAST(c."Classe" AS BIGINT) AS VARCHAR) = s.classe
            """
        else:
            query = f"SELECT * FROM {tbl_name}"
    else:
        query = f"SELECT * FROM {tbl_name}"

    df = conn.execute(query).df()
    conn.close()
    return df

with st.spinner("Carregando microdados do CAGED no DuckDB..."):
    df_caged = load_caged_data(table_name, nivel_selecionado)

if df_caged is None or df_caged.empty:
    st.info(f"Aguardando carregamento da tabela `{table_name}`.")
    st.stop()


# Garantir coluna de saldo
if "saldo" not in df_caged.columns and "Admitidos/Desligados" in df_caged.columns and "Count" in df_caged.columns:
    df_caged["saldo"] = df_caged["Admitidos/Desligados"] * df_caged["Count"]

# --- CARDS DE RESUMO (KPIs) ---
st.subheader(f"📊 Resumo do Emprego Formal na Paraíba - {ano_selecionado}")

col1, col2, col3, col4 = st.columns(4)

total_movimentacoes = int(df_caged["Count"].sum()) if "Count" in df_caged.columns else len(df_caged)
admitidos = int(df_caged[df_caged["Admitidos/Desligados"] == 1]["Count"].sum()) if "Admitidos/Desligados" in df_caged.columns else 0
desligados = int(df_caged[df_caged["Admitidos/Desligados"] == -1]["Count"].sum()) if "Admitidos/Desligados" in df_caged.columns else 0
saldo_total = int(df_caged["saldo"].sum()) if "saldo" in df_caged.columns else (admitidos - desligados)

with col1:
    st.metric("Saldo Líquido", f"{saldo_total:+d}", delta=f"{ano_selecionado}")
with col2:
    st.metric("Total de Admissões", f"{admitidos:,}".replace(",", "."))
with col3:
    st.metric("Total de Desligamentos", f"{desligados:,}".replace(",", "."))
with col4:
    st.metric("Total de Movimentações", f"{total_movimentacoes:,}".replace(",", "."))

st.markdown("---")

# --- ABAS DE ANÁLISE ---
tab_associacao, tab_mensal, tab_setores, tab_tabela = st.tabs([
    "🔗 Matriz de Associação (Compras x Emprego)", 
    "📅 Evolução Mensal CAGED", 
    "🏢 Maiores Setores (CNAE)", 
    "📋 Tabela Detalhada"
])

with tab_associacao:
    st.subheader("🔗 Associação entre Compras Públicas, Amparo Normativo e Emprego Formal")
    st.markdown("""
    Esta análise integra o **Processo Regulatório**, o **Volume de Compras do Estado** e o **Desempenho de Empregos (CAGED)**
    para responder à pergunta central: *Como os instrumentos de compras governamentais impactam o emprego e a estrutura produtiva da Paraíba?*
    """)

    @st.cache_data(ttl=300)
    def load_caged_compras_correlation(ano: int):
        conn = get_db_connection()
        tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
        
        # 1. Agrupamento de compras por Macro Setor Econômico (Usando dim_contratacoes_macro se disponível)
        if "dim_contratacoes_macro" in tables:
            query_compras_macro = f"""
                SELECT macro_setor, total_contratacoes, total_compras
                FROM dim_contratacoes_macro
                WHERE (ano_referencia = {ano} OR {ano} IS NULL)
            """
        else:
            query_compras_macro = f"""
                SELECT 
                    CASE 
                        WHEN LOWER(objeto) LIKE '%obra%' OR LOWER(objeto) LIKE '%construc%' OR LOWER(objeto) LIKE '%engenhar%' THEN 'F - Construção Civil'
                        WHEN LOWER(objeto) LIKE '%saude%' OR LOWER(objeto) LIKE '%medicament%' OR LOWER(objeto) LIKE '%hospital%' OR LOWER(objeto) LIKE '%tomograf%' OR LOWER(objeto) LIKE '%medico%' THEN 'Q - Saúde e Serviços Sociais'
                        WHEN LOWER(objeto) LIKE '%limpeza%' OR LOWER(objeto) LIKE '%vigilanc%' OR LOWER(objeto) LIKE '%seguranc%' OR LOWER(objeto) LIKE '%conservac%' THEN 'N - Serviços Admin / Vigilância / Limpeza'
                        WHEN LOWER(objeto) LIKE '%veicul%' OR LOWER(objeto) LIKE '%transporte%' OR LOWER(objeto) LIKE '%combustiv%' THEN 'H - Transporte e Logística'
                        WHEN LOWER(objeto) LIKE '%tecnologia%' OR LOWER(objeto) LIKE '%software%' OR LOWER(objeto) LIKE '%informatica%' OR LOWER(objeto) LIKE '%sistema%' THEN 'J - Informação e Comunicação (TI)'
                        WHEN LOWER(objeto) LIKE '%alimento%' OR LOWER(objeto) LIKE '%merenda%' OR LOWER(objeto) LIKE '%refeic%' THEN 'C - Indústria / Alimentação'
                        ELSE 'G - Comércio Varejista/Atacadista & Serviços Diversos'
                    END AS macro_setor,
                    COUNT(*) as total_contratacoes,
                    SUM(valorAdjudicado) as total_compras
                FROM contratacoes
                WHERE (ano_referencia = {ano} OR {ano} IS NULL) AND valorAdjudicado IS NOT NULL
                GROUP BY macro_setor
            """
        df_compras_macro = conn.execute(query_compras_macro).df()

        # 2. Agrupamento de saldo de empregos do CAGED por Seção correspondente
        caged_table = f"caged_pb_secao_{ano}"
        
        if caged_table in tables:
            query_caged_secao = f"""
                SELECT 
                    CASE 
                        WHEN "Seção" = 'F' THEN 'F - Construção Civil'
                        WHEN "Seção" = 'Q' THEN 'Q - Saúde e Serviços Sociais'
                        WHEN "Seção" = 'N' THEN 'N - Serviços Admin / Vigilância / Limpeza'
                        WHEN "Seção" = 'H' THEN 'H - Transporte e Logística'
                        WHEN "Seção" = 'J' THEN 'J - Informação e Comunicação (TI)'
                        WHEN "Seção" = 'C' THEN 'C - Indústria / Alimentação'
                        ELSE 'G - Comércio Varejista/Atacadista & Serviços Diversos'
                    END AS macro_setor,
                    SUM(saldo) as saldo_empregos
                FROM {caged_table}
                GROUP BY macro_setor
            """
            df_caged_macro = conn.execute(query_caged_secao).df()
        else:
            df_caged_macro = pd.DataFrame(columns=["macro_setor", "saldo_empregos"])

        conn.close()

        # Merge de Compras com Saldo do CAGED por Macro Setor
        df_merged = pd.merge(df_compras_macro, df_caged_macro, on="macro_setor", how="outer").fillna(0)
        return df_merged

    df_cross = load_caged_compras_correlation(ano_selecionado)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f"##### 💰 1. Volume de Compras Públicas por Setor (R\$ - {ano_selecionado})")
        if not df_cross.empty:
            df_cross_sorted = df_cross.sort_values("total_compras", ascending=False)
            fig_compras = px.bar(
                df_cross_sorted,
                y="macro_setor",
                x="total_compras",
                orientation="h",
                text="total_compras",
                color="total_compras",
                hover_name="macro_setor",
                labels={"macro_setor": "Setor Econômico", "total_compras": "Valor Adjudicado (R$)"},
                color_continuous_scale="Blues"
            )
            fig_compras.update_traces(texttemplate='R$ %{text:,.2s}', textposition='outside')
            fig_compras.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
            st.plotly_chart(fig_compras, width="stretch")
        else:
            st.info("Sem dados de compras para o ano selecionado.")

    with c2:
        st.markdown(f"##### 💼 2. Saldo de Empregos Formais no Mesmo Setor (CAGED - {ano_selecionado})")
        if not df_cross.empty:
            fig_empregos = px.bar(
                df_cross_sorted,
                y="macro_setor",
                x="saldo_empregos",
                orientation="h",
                text="saldo_empregos",
                color="saldo_empregos",
                hover_name="macro_setor",
                labels={"macro_setor": "Setor Econômico", "saldo_empregos": "Saldo de Empregos (CAGED)"},
                color_continuous_scale=["#d9534f", "#5cb85c"]
            )
            fig_empregos.update_traces(texttemplate='%{text:+d}', textposition='outside')
            fig_empregos.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
            st.plotly_chart(fig_empregos, width="stretch")
        else:
            st.info("Sem dados de saldo do CAGED para o ano selecionado.")


    st.markdown("---")
    st.markdown("### 🗺️ Origem Geográfica dos Fornecedores & Retenção Territorial de Renda")
    
    @st.cache_data(ttl=300)
    def load_fornecedores_uf_data(ano: int):
        conn = get_db_connection()
        tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]

        if "dim_fornecedores_uf_resumo" in tables:
            query_uf = f"""
                SELECT 
                    uf,
                    origem_tipo,
                    num_empresas,
                    valor_total_contratado
                FROM dim_fornecedores_uf_resumo
                WHERE ano_referencia = {ano} OR {ano} IS NULL
                ORDER BY valor_total_contratado DESC
            """
        elif "dim_fornecedores_uf" in tables:
            query_uf = f"""
                WITH base AS (
                    SELECT 
                        f.uf,
                        CASE WHEN f.uf = 'PB' THEN 'Paraíba (Retenção Local)' ELSE 'Outras UFs (Vazamento de Renda)' END as origem_tipo,
                        f.cnpj,
                        c.valorTotal
                    FROM dim_fornecedores_uf f
                    JOIN contratos c ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = f.cnpj
                    WHERE c.ano_referencia = {ano} OR {ano} IS NULL
                )
                SELECT 
                    uf,
                    origem_tipo,
                    COUNT(DISTINCT cnpj) as num_empresas,
                    SUM(valorTotal) as valor_total_contratado
                FROM base
                GROUP BY uf, origem_tipo
                ORDER BY valor_total_contratado DESC
            """
        else:
            conn.close()
            return None, 0.0

        df_uf = conn.execute(query_uf).df()

        if not df_uf.empty:
            total_geral = df_uf["valor_total_contratado"].sum()
            total_pb = df_uf[df_uf["uf"] == "PB"]["valor_total_contratado"].sum() if "PB" in df_uf["uf"].values else 0
            pct_pb = (total_pb * 100.0 / total_geral) if total_geral > 0 else 0.0
        else:
            pct_pb = 0.0

        conn.close()
        return df_uf, float(pct_pb)

    df_uf, pct_retencao = load_fornecedores_uf_data(ano_selecionado)



    if df_uf is not None and not df_uf.empty:
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
        
        val_pb = df_uf[df_uf["uf"] == "PB"]["valor_total_contratado"].sum() if "PB" in df_uf["uf"].values else 0
        val_outros = df_uf[df_uf["uf"] != "PB"]["valor_total_contratado"].sum()
        
        with col_kpi1:
            st.metric("Taxa de Retenção Territorial (PB)", f"{pct_retencao:.1f}%", help="Percentual dos recursos de compras públicas que permanecem com fornecedores sediados na Paraíba")
        with col_kpi2:
            st.metric("Volume Retido na PB", f"R$ {val_pb:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with col_kpi3:
            st.metric("Vazamento para Outras UFs", f"R$ {val_outros:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        col_uf1, col_uf2 = st.columns(2)
        
        # Agrupa as Top 5 UFs e consolida o restante como "Outras UFs" para despoluir a rosca
        df_top5 = df_uf.head(5).copy()
        outras_val = df_uf.iloc[5:]["valor_total_contratado"].sum() if len(df_uf) > 5 else 0
        outras_emp = df_uf.iloc[5:]["num_empresas"].sum() if len(df_uf) > 5 else 0
        
        if outras_val > 0:
            df_pie = pd.concat([
                df_top5,
                pd.DataFrame([{
                    "uf": "Outras UFs",
                    "origem_tipo": "Outras UFs (Vazamento de Renda)",
                    "num_empresas": outras_emp,
                    "valor_total_contratado": outras_val
                }])
            ], ignore_index=True)
        else:
            df_pie = df_top5

        with col_uf1:
            st.markdown("##### 📍 Distribuição de Compras por Estado (Top 5 UFs + Outras)")
            fig_uf_pie = px.pie(
                df_pie,
                names="uf",
                values="valor_total_contratado",
                hover_data=["num_empresas"],
                labels={"uf": "Estado (UF)", "valor_total_contratado": "Valor Contratado (R$)", "num_empresas": "Empresas"},
                color="uf",
                color_discrete_map={
                    "PB": "#2ca02c",      # Verde para Paraíba (Local)
                    "SP": "#1f77b4",      # Azul para SP
                    "PE": "#ff7f0e",      # Laranja para PE
                    "CE": "#9467bd",      # Roxo para CE
                    "RN": "#8c564b",      # Marrom para RN
                    "Outras UFs": "#d62728" # Vermelho em destaque para Outras UFs
                },
                hole=0.4
            )
            fig_uf_pie.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_uf_pie, width="stretch")


        with col_uf2:
            st.markdown("##### 🏙️ Principais Estados de Origem dos Fornecedores")
            fig_uf_bar = px.bar(
                df_uf.head(10),
                x="uf",
                y="valor_total_contratado",
                color="origem_tipo",
                text="valor_total_contratado",
                color_discrete_map={"Paraíba (Retenção Local)": "#2ca02c", "Outras UFs (Vazamento de Renda)": "#1f77b4"},
                labels={"uf": "UF do Fornecedor", "valor_total_contratado": "Valor Total Contratado (R$)"}
            )
            fig_uf_bar.update_traces(texttemplate='R$ %{text:,.2s}', textposition='outside')
            st.plotly_chart(fig_uf_bar, width="stretch")
    else:
        st.info("Painel de retração territorial em sincronização...")

    st.markdown("---")
    st.markdown("### 📊 Análise Interpretativa: Efeito do Gasto Público no Emprego Formal")
    
    st.markdown("""
    A comparação direta entre o **Volume de Compras Públicas (R\$)** e o **Saldo Líquido de Empregos (CAGED)** por setor econômico revela dinâmicas fundamentais para a formulação da **Estratégia Nacional de Contratações Públicas (ENCP)** na Paraíba:

    #### 1. 🏗️ Construção Civil (Infraestrutura vs. Absorção de Mão de Obra)
    - **Constatação**: Apresenta um dos maiores volumes de recursos adjudicados pelo Estado (bilhões em obras e engenharia), porém o **saldo de empregos formais gerados mostra-se desproporcionalmente modesto ou moderado**.
    - **Leitura Teórica (Keynes & Furtado)**: O gasto em grandes obras públicas atua fortemente na injeção de liquidez na economia, mas possui alta intensidade de capital em máquinas e materiais. Sem cláusulas contratuais de contratação local e acompanhamento de encadeamento produtivo, parte expressiva do recurso 'vaza' da economia regional sem produzir a retenção esperada em postos de trabalho permanentes.

    #### 2. 🧹 Serviços Administrativos, Vigilância e Limpeza (Alta Intensidade de Trabalho)
    - **Constatação**: Exige uma fatia orçamentária menor ou intermediária em termos de valor total licitado, mas apresenta um **alto volume absoluto de saldo de empregos mantidos e gerados**.
    - **Leitura Teórica (Keynes)**: Representa o uso do poder de compra governamental como **demanda efetiva direta de trabalho**. São setores altamente intensivos em mão de obra de baixa/média qualificação, cruciais para a circulação rápida de renda nas periferias urbanas.

    #### 3. 💡 Informação, Comunicação e Tecnologia (Transformação Produtiva & Schumpeter)
    - **Constatação**: Os aportes em licitações de tecnologia e sistemas representam uma parcela ainda tímida do gasto global, refletindo em saldos de emprego focados em nichos específicos.
    - **Leitura Teórica (Schumpeter)**: O desafio do Estado está em utilizar o **Marco Legal das Startups e os CPSI (Lei 182/2021)** para direcionar esse gasto a empresas locais de tecnologia, estimulando a contratação de empregos qualificados de maior valor agregado e evitando a mera importação de licenças de software de multinacionais externas.

    ---
    > 💡 **Conclusão Metodológica para os Formuladores de Política**:
    > *Não basta avaliar o valor bruto licitado pelo Estado. É indispensável analisar o **multiplicador de emprego e a complexidade tecnológica** dos setores contratados para garantir que as compras públicas atuem verdadeiramente na transformação da estrutura produtiva da Paraíba.*
    """)



with tab_mensal:
    st.subheader("Evolução Mensal do Saldo de Empregos Formais")
    if "mes" in df_caged.columns and "saldo" in df_caged.columns:
        meses_map = {
            "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
            "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
            "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"
        }
        df_mensal = df_caged.groupby("mes")["saldo"].sum().reset_index()
        df_mensal["mes_code"] = df_mensal["mes"].astype(str).str.zfill(2)
        df_mensal = df_mensal.sort_values("mes_code")
        df_mensal["mes_label"] = df_mensal["mes_code"].map(meses_map)

        fig_mensal = px.bar(
            df_mensal,
            x="mes_label",
            y="saldo",
            text="saldo",
            labels={"mes_label": "Mês", "saldo": "Saldo de Empregos"},
            title=f"Saldo Líquido de Empregos por Mês ({ano_selecionado})",
            color="saldo",
            color_continuous_scale=["#d9534f", "#f0ad4e", "#5cb85c"]
        )
        fig_mensal.update_traces(texttemplate='%{text:+d}', textposition='outside')
        fig_mensal.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_mensal, width="stretch")
    else:
        st.info("Coluna de mês ou saldo não disponível para este nível.")

with tab_setores:
    st.subheader("Top 10 Classes CNAE com Maior e Menor Saldo de Empregos")
    
    has_classe_code = "Classe" in df_caged.columns
    col_sector_name = "nome_classe" if "nome_classe" in df_caged.columns else ("Seção" if "Seção" in df_caged.columns else "Classe")
    
    if col_sector_name in df_caged.columns and "saldo" in df_caged.columns:
        group_cols = [col_sector_name]
        if has_classe_code and col_sector_name != "Classe":
            group_cols.append("Classe")
            
        df_setores = df_caged.groupby(group_cols)["saldo"].sum().reset_index()
        
        # Limpa o código da classe (remove .0) e cria rótulo amigável
        df_setores["nome_completo"] = df_setores[col_sector_name]
        if has_classe_code:
            df_setores["classe_clean"] = df_setores["Classe"].astype(str).str.replace(".0", "", regex=False)
            df_setores["eixo_y_label"] = df_setores.apply(lambda r: f"[{r['classe_clean']}] " + (str(r[col_sector_name])[:32] + "..." if len(str(r[col_sector_name])) > 35 else str(r[col_sector_name])), axis=1)
        else:
            df_setores["eixo_y_label"] = df_setores[col_sector_name].apply(lambda x: str(x)[:35] + "..." if len(str(x)) > 38 else str(x))

        top_ganhadores = df_setores.sort_values("saldo", ascending=False).head(10)
        top_perdedores = df_setores.sort_values("saldo", ascending=True).head(10)

        col_g, col_p = st.columns(2)

        with col_g:
            st.markdown("##### 🟢 Top 10 Setores em Geração de Empregos")
            fig_g = px.bar(
                top_ganhadores,
                y="eixo_y_label",
                x="saldo",
                orientation="h",
                text="saldo",
                color="saldo",
                hover_name="nome_completo",
                hover_data={"eixo_y_label": False, "saldo": True},
                labels={"eixo_y_label": "Classe CNAE", "saldo": "Saldo de Empregos"},
                color_continuous_scale="Greens"
            )
            fig_g.update_traces(texttemplate='%{text:+d}', textposition='outside')
            fig_g.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
            st.plotly_chart(fig_g, width="stretch")

        with col_p:
            st.markdown("##### 🔴 Top 10 Setores em Redução de Empregos")
            fig_p = px.bar(
                top_perdedores,
                y="eixo_y_label",
                x="saldo",
                orientation="h",
                text="saldo",
                color="saldo",
                hover_name="nome_completo",
                hover_data={"eixo_y_label": False, "saldo": True},
                labels={"eixo_y_label": "Classe CNAE", "saldo": "Saldo de Empregos"},
                color_continuous_scale="Reds_r"
            )
            fig_p.update_traces(texttemplate='%{text:+d}', textposition='outside')
            fig_p.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
            st.plotly_chart(fig_p, width="stretch")

with tab_tabela:
    st.subheader("Explorador de Dados Brutos do CAGED")
    st.dataframe(df_caged, width="stretch")



