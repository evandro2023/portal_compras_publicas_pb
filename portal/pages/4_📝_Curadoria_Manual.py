import streamlit as st
import pandas as pd
import os
import hashlib
from utils import set_page_config, render_custom_css, render_sidebar_docs

set_page_config(page_title="Curadoria Manual - Portal de Compras Públicas PB")
render_custom_css()
render_sidebar_docs()

import duckdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANDIDATAS_CSV = os.path.join(BASE_DIR, "outputs", "tables", "candidatas_normas.csv")
CATALOGO_CSV = os.path.join(BASE_DIR, "data", "catalogo_curado_leis.csv")
DB_PATH = os.path.join(BASE_DIR, "data", "compras_pb.duckdb")

# --- Autenticação ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_nome" not in st.session_state:
    st.session_state["user_nome"] = ""
if "user_unidade" not in st.session_state:
    st.session_state["user_unidade"] = ""

def authenticate(user_id, password):
    if not os.path.exists(DB_PATH):
        return None
    try:
        conn = duckdb.connect(DB_PATH, read_only=True)
        res = conn.execute("""
            SELECT nome, unidade FROM usuarios_curadores 
            WHERE id_nome = ? AND senha = ?
        """, [user_id.strip(), password.strip()]).fetchone()
        conn.close()
        return res
    except Exception as e:
        return None

def login():
    st.title("🔒 Acesso Restrito - Módulo de Curadoria")
    st.markdown("Este módulo é de acesso restrito aos curadores autorizados no banco de dados do projeto.")
    
    with st.form("login_form"):
        user = st.text_input("Usuário (id_nome)")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            user_data = authenticate(user, password)
            if user_data:
                st.session_state["authenticated"] = True
                st.session_state["username"] = user
                st.session_state["user_nome"] = user_data[0]
                st.session_state["user_unidade"] = user_data[1]
                st.success(f"Bem-vindo(a), {user_data[0]}!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos! Verifique suas credenciais de curador.")

def logout():
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["user_nome"] = ""
    st.session_state["user_unidade"] = ""
    st.rerun()

if not st.session_state["authenticated"]:
    login()
    st.stop()

# --- Cabeçalho e Descrição do Módulo ---
st.sidebar.markdown(f"**Usuário:** `{st.session_state['user_nome']}`")
st.sidebar.markdown(f"**Unidade:** `{st.session_state['user_unidade']}`")
if st.sidebar.button("🚪 Sair (Logout)"):
    logout()

st.title("📝 Módulo de Curadoria e Validação Normativa")
st.subheader(f"👋 Olá, {st.session_state['user_nome']} ({st.session_state['user_unidade']})!")

st.markdown("""
### Papel do Curador Metodológico
Como **Curador do Portal**, seu papel é crucial para garantir a **consistência metodológica e jurídica** da base oficial de dados do projeto. 

As normas listadas abaixo foram identificadas automaticamente via algoritmos de raspagem (Skill de Monitoramento) e buscas exploratórias nos Diários Oficiais e Portais de Transparência da Paraíba, Sergipe e Governo Federal.

#### Suas Atribuições:
1. **Análise de Conteúdo & Aderência**: Avaliar a descrição da norma e determinar seu grau de relevância para o desenvolvimento regional, inovação, sustentabilidade ou contas públicas.
2. **Classificação de Status**:
   - 🟡 **A ser revisado (pendente)**: Norma recém-descoberta aguardando triagem.
   - 🔵 **Revisando**: Norma sob análise ativa ou consulta a pareceres técnicos.
   - 🟢 **Revisada**: Norma aprovada e homologada para compor a **Base Oficial do Projeto** (`catalogo_curado_leis.csv`).
3. **Incorporação Oficial**: Ao marcar uma norma como **Revisada** e salvar, ela será promovida para o Catálogo Curado Oficial, ficando disponível para os cálculos do IAAN, Matriz Comparativa e Painéis de Compras.
""")

st.markdown("<hr style='border-top: 2px solid #0056b3; margin-top: 10px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# --- Carregamento dos Dados ---
if not os.path.exists(CANDIDATAS_CSV):
    st.info("Nenhuma norma candidata pendente de revisão no momento.")
    st.stop()

df_candidatas = pd.read_csv(CANDIDATAS_CSV, dtype=str).fillna("")

if df_candidatas.empty:
    st.success("🎉 Todas as normas candidatas já foram revisadas e integradas!")
    st.stop()

# Garantir tipos de dados explicitamente para compatibilidade com st.data_editor
for col in ["esfera", "identificador", "título", "tema detectado", "URL", "fonte", "status_revisao"]:
    if col in df_candidatas.columns:
        df_candidatas[col] = df_candidatas[col].astype(str)

# Mapeamento de status com identificadores visuais/coloridos
status_mapping = {
    "pendente": "🟡 A ser revisado",
    "A ser revisado": "🟡 A ser revisado",
    "revisando": "🔵 Revisando",
    "revisada": "🟢 Revisada",
    "": "🟡 A ser revisado"
}

if "status_revisao" not in df_candidatas.columns:
    df_candidatas["status_revisao"] = "🟡 A ser revisado"
else:
    df_candidatas["status_revisao"] = df_candidatas["status_revisao"].map(lambda x: status_mapping.get(str(x).strip(), "🟡 A ser revisado"))

st.subheader("📋 Tabela de Normas Candidatas a Curadoria")
st.markdown("Altere o **Status de Curadoria** das normas diretamente na tabela abaixo. Selecione **🟢 Revisada** para integrar a norma à base oficial do projeto.")

# Opções de Status com cores
status_options = ["🟡 A ser revisado", "🔵 Revisando", "🟢 Revisada"]

# Tabela Interativa
edited_df = st.data_editor(
    df_candidatas,
    column_config={
        "esfera": st.column_config.SelectboxColumn("Esfera", options=["PB", "SE", "Federal"], required=True),
        "identificador": st.column_config.TextColumn("Identificador", required=True),
        "ano": st.column_config.TextColumn("Ano"),
        "título": st.column_config.TextColumn("Descrição / Título do Conteúdo", width="medium"),
        "tema detectado": st.column_config.TextColumn("Tema Detectado"),
        "URL": st.column_config.LinkColumn("Link Oficial", display_text="Acessar PDF/Link"),
        "fonte": st.column_config.TextColumn("Fonte"),
        "status_revisao": st.column_config.SelectboxColumn(
            "Status de Curadoria",
            options=status_options,
            required=True,
            help="Altere para '🟢 Revisada' para promover a norma para o catálogo oficial."
        )
    },
    use_container_width=True,
    num_rows="dynamic",
    key="editor_candidatas"
)

# --- Processamento e Salvamento ---
if st.button("💾 Salvar Alterações e Processar Aprovações", type="primary"):
    revisadas = edited_df[edited_df["status_revisao"] == "🟢 Revisada"]
    mantidas = edited_df[edited_df["status_revisao"] != "🟢 Revisada"]
    
    if not revisadas.empty:
        # Carregar catálogo oficial
        if os.path.exists(CATALOGO_CSV):
            df_catalogo = pd.read_csv(CATALOGO_CSV)
        else:
            df_catalogo = pd.DataFrame(columns=[
                "esfera", "identificador", "ano", "tipo", "tema_principal", "url_oficial", "status_revisao", "hash_documento"
            ])
            
        novos_registros = []
        for idx, row in revisadas.iterrows():
            # Inferir tipo de norma
            ident = str(row["identificador"])
            if "Decreto" in ident:
                tipo = "Decreto"
            elif "Lei" in ident:
                tipo = "Lei"
            elif "IN" in ident or "Instrução" in ident:
                tipo = "Instrução Normativa"
            elif "Portaria" in ident:
                tipo = "Portaria"
            elif "ON" in ident or "Orientação" in ident:
                tipo = "Orientação Normativa"
            else:
                tipo = "Outros"
                
            tema = row["tema detectado"] if pd.notna(row["tema detectado"]) and str(row["tema detectado"]).strip() != "" else row.get("título", "")
            url = row["URL"] if pd.notna(row["URL"]) else ""
            ano = row["ano"] if pd.notna(row["ano"]) else ""
            
            # Geração do Hash Único (Preserva histórico e alterações da norma)
            hash_input = f"{row['esfera']}_{row['identificador']}_{ano}_{tema}_{url}".encode("utf-8")
            hash_doc = hashlib.sha256(hash_input).hexdigest()
            
            novos_registros.append({
                "esfera": row["esfera"],
                "identificador": row["identificador"],
                "ano": int(ano) if str(ano).isdigit() else ano,
                "tipo": tipo,
                "tema_principal": tema,
                "url_oficial": url,
                "status_revisao": "revisado",
                "hash_documento": hash_doc
            })
            
        df_novos = pd.DataFrame(novos_registros)
        
        # Deduplica pelo HASH ou pela combinação de (esfera, identificador, ano, url) para permitir histórico de normas alteradoras
        df_catalogo_atualizado = pd.concat([df_catalogo, df_novos], ignore_index=True)
        df_catalogo_atualizado = df_catalogo_atualizado.drop_duplicates(subset=["esfera", "identificador", "ano", "url_oficial"])
        df_catalogo_atualizado.to_csv(CATALOGO_CSV, index=False)
        
        st.success(f"✅ {len(revisadas)} norma(s) aprovada(s) e incorporada(s) com sucesso à Base Oficial do Projeto (`data/catalogo_curado_leis.csv`)!")
    
    # Atualizar lista de candidatas
    mantidas.to_csv(CANDIDATAS_CSV, index=False)
    st.info("📌 Tabela de candidatas pendentes atualizada.")
    st.rerun()
