import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import set_page_config

set_page_config("Dados Socioeconômicos")

st.title("📈 Módulo: Impacto Socioeconômico")

st.markdown("""
Integração com bases externas para contextualizar o impacto das compras governamentais.

**Bases Previstas:**
- **RAIS:** Vínculos formais e massa salarial.
- **CAGED:** Admissões e desligamentos.
- **PIB:** Contas regionais dos municípios da PB.
- **CEMPRE:** Empresas e pessoal ocupado.
- **Comex Stat:** Exportações e importações.
""")

st.warning("Módulo sob planejamento. Integração com DuckDB em desenvolvimento.")
