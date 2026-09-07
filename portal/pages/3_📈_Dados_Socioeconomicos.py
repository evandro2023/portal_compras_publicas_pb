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

# Função cached para obter lista de tabelas e anos disponíveis no DuckDB
@st.cache_data(ttl=300)
def get_caged_metadata():
    conn = get_db_connection()
    tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
    conn.close()

    caged_tables = [t for t in tables if t.startswith("caged_pb_")]
    return caged_tables

try:
    caged_tables = get_caged_metadata()
except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados DuckDB: {e}")
    st.stop()

if not caged_tables:
    st.warning("⚠️ Os dados do CAGED estão sendo processados e carregados no banco de dados. Por favor, recarregue a página em alguns instantes.")
    st.info("Status da ingestão: Processando microdados de 2025 e 2026 em segundo plano...")
    st.stop()

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
    
    if tbl_name not in tables:
        conn.close()
        return None

    if nivel == "classe" and "caged_secao_classe" in tables:
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


    
    df = conn.execute(query).df()
    conn.close()
    return df

with st.spinner("Carregando microdados do CAGED no DuckDB..."):
    df_caged = load_caged_data(table_name, nivel_selecionado)

if df_caged is None or df_caged.empty:
    st.info(f"Tabela `{table_name}` ainda não foi gerada ou está sendo carregada no banco DuckDB.")
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
        
        # 1. Agrupamento de compras por Macro Setor Econômico
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
        tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
        
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



