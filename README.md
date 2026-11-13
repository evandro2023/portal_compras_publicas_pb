# Portal Compras Públicas PB 📊

Este projeto visa criar uma ferramenta analítica avançada para acompanhar e analisar as compras públicas realizadas pelo governo do Estado da Paraíba. O projeto é dividido em módulos integrados (ETL / Teoria Econômica / CAGED / Visualização Streamlit):

1. **Coleta de Legislação (Catálogo Ouro)**: `scripts/coleta_leis.py` faz o parse e download automático das normas essenciais (Federal e Estadual) para cruzamento posterior.
2. **Coleta de Dados de Compras**: `scripts/explora_api_compras_pb.py` varre as APIs governamentais (em modo exploratório ou incremental) e constrói as bases em CSV bruto.
3. **Modelagem Econômica e Risco**: O script `src/etl/enriquecimento_socioeconomico.py` limpa textos e constrói um Star Schema com matrizes clássicas (Keynes, Furtado, Schumpeter) e análises de Risco Metodológico.
4. **Ingestão de Dados Econômicos (CAGED PB)**: `src/caged/ingest_caged.py` baixa e consolida os microdados formais de emprego da Paraíba (2025/2026) nos níveis CNAE de Seção, **Classe (4 dígitos)** e Subclasse, armazenando em Parquet e DuckDB.
5. **Enriquecimento de Localização dos Fornecedores (UF/Município)**: `src/etl/enriquece_fornecedores_uf.py` consulta as APIs de Dados Abertos da Receita Federal (MinhaReceita) para identificar a UF de origem dos fornecedores e calcular a taxa de retenção territorial de renda da Paraíba.
6. **Mapeamento de CNAE, Setor e Intensidade Tecnológica**: `src/etl/cnae_catalog.py` e `src/etl/enriquece_cnae_setor.py` aplicam taxonomias IBGE e OCDE para classificar contratados por 7 setores econômicos (Extrativa, Transformação, SIUP, Construção, Comércio, Serviços, Agro), 4 níveis de intensidade tecnológica e faixas de localização (Capital PB, Interior PB, Nordeste, Fora do Nordeste).
7. **ETL e DuckDB (Analytics)**: `src/etl/build_db.py` transforma toda a massa de CSVs, Parquets e cruzamentos de Teoria vs Gastos em uma base de dados local de alta velocidade (`compras_pb.duckdb`).
8. **Portal Web Streamlit (Multipage)**: Dashboard interativo com Módulo de Compras Públicas, Perfil Produtivo e CNAE, Módulo de Base Legal, Módulo Socioeconômico e Módulo de Curadoria Manual.
9. **Módulo de Curadoria Manual (Autenticado)**: Interface para curadores revisarem, alterarem status (A ser revisado, revisando, revisada) e integrarem novas normas candidatas ao catálogo curado oficial.

---

## 🚀 Como Executar o Projeto

O projeto utiliza a ferramenta moderna `uv` para gestão ultrarrápida de dependências e ambientes virtuais.

### 1. Pré-requisitos
- Tenha o [uv](https://docs.astral.sh/uv/) instalado na sua máquina.

### 2. Instalação
Na raiz do projeto, instale todas as bibliotecas executando:
```bash
uv sync
```
Isso criará a pasta `.venv` automaticamente lendo o `pyproject.toml`.

### 3. Executando as Coletas e Ingestão de Dados

**Passo A: Coletar a Legislação**
```bash
uv run scripts/coleta_leis.py --baixar
```

**Passo B: Extrair Dados da API da Paraíba**
```bash
uv run scripts/explora_api_compras_pb.py --limite-paginas 0
```

> Para atualizar aditivos de contratos de anos anteriores (o modo `--incremental` só busca o ano corrente), recarregue os contratos por completo:
> ```bash
> uv run scripts/explora_api_compras_pb.py --limite-paginas 0 --endpoints /contratos --anos 2024 2025 2026
> ```
> Depois, reconstrua o banco (aplica automaticamente a deduplicação de contratos e os enriquecimentos de socioeconomia e UF dos fornecedores):
> ```bash
> PYTHONPATH=. uv run python src/etl/build_db.py
> ```

**Passo C: Ingerir Microdados do CAGED (Paraíba)**
```bash
PYTHONPATH=. uv run python src/caged/ingest_caged.py --incremental
```

**Passo D: Enriquecer Localização dos Fornecedores (UF/Município)**
```bash
PYTHONPATH=. uv run python src/etl/enriquece_fornecedores_uf.py
```

**Passo E: Processar Enriquecimento por CNAE, Setor e Intensidade Tecnológica**
```bash
PYTHONPATH=. uv run python src/etl/enriquece_cnae_setor.py
```

**Passo F: Rodar a Aplicação Web no Streamlit**
```bash
PYTHONPATH=. uv run streamlit run portal/app.py
```

---

## 🔄 Fluxo de Atualização de Dados (Automático vs. Manual)

### 1. Atualização Automática (Robô / CI/CD)
O projeto conta com automação via **GitHub Actions** configurada no arquivo [`.github/workflows/atualiza_dados.yml`](.github/workflows/atualiza_dados.yml):
- **Periodicidade:** Toda segunda-feira às 01:00 UTC (22:00 de domingo no horário de Brasília).
- **O que faz:**
  1. Executa `scripts/explora_api_compras_pb.py --limite-paginas 0 --incremental` consultando a API do Governo do Estado da Paraíba para capturar novos registros do ano corrente.
  2. Executa `src/etl/build_db.py`, que deduplica contratos, calcula matrizes teóricas e gera o arquivo consolidado `data/compras_pb.duckdb`.
  3. Faz commit e envia (`git push`) as novas bases de dados para o repositório no GitHub (`origin/main`).
- **Streamlit Cloud:** Detecta automaticamente o novo commit na branch `main` e reinicia o painel já com os dados atualizados.

---

### 2. Para Quem Trabalha Localmente
Se você desenvolve ou roda o portal na sua máquina:
- **Rotina semanal normal:** Você **NÃO** precisa reprocessar toda a raspagem da API. Basta sincronizar seu repositório local:
  ```bash
  git pull origin main
  ```
  Isso já trará o banco `data/compras_pb.duckdb` e os arquivos CSV brutos prontos e atualizados.

---

### 3. Quando e Como Fazer Atualização Manual

Você só precisa rodar o pipeline manualmente se desejar:
1. **Antecipar dados:** Buscar dados da API imediatamente sem esperar pela execução de segunda-feira.
2. **Atualizar aditivos de contratos de anos anteriores (2024 e 2025):** Como a rotina semanal roda em modo `--incremental` (apenas ano vigente), novos aditivos assinados em 2026 para contratos de 2024/2025 requerem busca completa dos contratos.
3. **Novas empresas / enriquecimento CNAE:** Atualizar dados cadastrais de novos CNPJs que surgiram na base.

#### Passo a passo para atualização manual completa:

```bash
# 1. Extrair contratos de todos os anos (atualiza aditivos retroativos)
uv run scripts/explora_api_compras_pb.py --limite-paginas 0 --endpoints /contratos --anos 2024 2025 2026

# 2. Reconstruir a base analítica DuckDB (executa dedup_contratos.py e constrói star schema)
PYTHONPATH=. uv run python src/etl/build_db.py

# 3. Enriquecer localização e dados Receita Federal dos novos fornecedores
PYTHONPATH=. uv run python src/etl/enriquece_fornecedores_uf.py

# 4. Atualizar taxonomia CNAE, 7 setores econômicos e intensidade tecnológica
PYTHONPATH=. uv run python src/etl/enriquece_cnae_setor.py

# 5. (Opcional) Atualizar legislação do catálogo ouro
uv run scripts/coleta_leis.py --baixar
```


---

## 🗂️ Estrutura de Diretórios

- `/data/`: Base de dados, catálogo curado, DuckDB e CSVs/Parquets brutos e processados (`raw` e `processed`).
- `/scripts/`: Scripts utilitários de web scraping e consumo de APIs (`coleta_leis.py`, `explora_api_compras_pb.py`, `valida_cagepa_planilha.py`).
- `/src/caged/`: Ingestão, tratamento e consolidação do Novo CAGED (`data.py`, `ingest_caged.py`, `secao_classe.csv`).
- `/src/etl/`: Lógica de transformação, enriquecimento socioeconômico e carga (`build_db.py`, `dedup_contratos.py`, `cnae_catalog.py`, `enriquecimento_socioeconomico.py`, `enriquece_fornecedores_uf.py`, `enriquece_cnae_setor.py`).
- `/portal/`: Aplicação interativa web Streamlit (Painel Multipage).
  - `app.py`: Página inicial (Home) com apresentação do projeto e equipe.
  - `pages/1_🛍️_Compras_Publicas.py`: Módulo 1 (Dashboard de Contratações, Contratos e Fornecedores com Top 100 maiores contratos ordenados por valor).
  - `pages/2_⚖️_Base_Legal.py`: Módulo 2 (Matrizes de IAAN, Comparação PBxSE e Aderência Teórica).
  - `pages/3_📈_Dados_Socioeconomicos.py`: Módulo 3 (Matriz de Associação Compras x Emprego, Retenção Territorial de Renda por UF, Evolução Mensal do CAGED e Rankings por Classe CNAE).
  - `pages/4_📝_Curadoria_Manual.py`: Módulo 4 (Interface de Login e Curadoria para Triagem, Revisão e Validação da Base Oficial).
  - `pages/5_🏭_Perfil_Produtivo_CNAE.py`: Módulo 5 (Análise por CNAE, CNPJ, Localização Geográfica, 7 Setores Econômicos, Intensidade Tecnológica OCDE/IBGE, com filtros por Órgão Contratante, Modalidade de Compra e Porte ME/EPP).
- `/outputs/`: Relatórios gerenciais e extrações analíticas.
  - `outputs/relatorio/`: Relatórios técnicos executivos consolidados em PDF e HTML (`relatorio_analise_gt_compras_pb.pdf` para o Grupo de Trabalho).
  - `outputs/tables/`: Extrações tabulares completas em XLS (`bens_servicos_nivel_contratos.xls`, `bens_servicos_itens_contratados.xls`, `dados_consolidado.xls`).
  - `outputs/merenda/`: Análise exploratória sobre PNAE / Merenda Escolar na Secretaria de Educação.
  - `outputs/validacao_cagepa/`: Relatórios de conferência cruzada CAGEPA x Diário Oficial.
- `/documentacao/`: Referenciais teóricos, relatórios em PDF e guia de ingestão do CAGED (`estrategia_ingestao_caged.md`).

---

## 📈 Status de Desenvolvimento

- **[✓] Banco Analítico (DuckDB):** Estruturado com tabelas de compras, matrizes teóricas, séries do CAGED, dimensões geográficas e visão `vw_analise_compras_cnae_localizacao`. Resiliência de concorrência com fallback automático de leitura em `portal/utils.py`.
- **[✓] Módulo 1 (Compras Públicas):** Implementado com consultas SQL rápidas, ranking dos Top 100 maiores contratos e filtros sincronizados de órgãos (incluindo estatais como CAGEPA).
- **[✓] Módulo 2 (Base Legal):** Matrizes visuais de IAAN e comparativo PB x SE.
- **[✓] Módulo 3 (Dados Econômicos - CAGED & Retenção Territorial):** Mapeamento por Classe CNAE, Matriz de Associação Compras x Emprego e Taxa de Retenção Territorial de Renda por UF.
- **[✓] Módulo 4 (Curadoria Manual):** Módulo restrito com autenticação para revisão e homologação de normas para a base oficial.
- **[✓] Módulo 5 (Perfil Produtivo & CNAE):** Mapeamento por CNPJ, CNAE, Localização (Capital PB, Interior PB, Nordeste, Fora do Nordeste), 7 Setores Econômicos e Intensidade Tecnológica OCDE/IBGE. Inclui filtros por Órgão, Modalidade de Compra, Porte Empresarial (ME/EPP) e KPI de participação de MPEs.
- **[✓] Atendimento às Demandas do Grupo de Trabalho (GT):** Consultas analíticas multidimensionais cruzando bens e serviços, CNAE, OCDE, CNPJ, Órgãos, Modalidades e enquadramento de Micro e Pequenas Empresas (ME/EPP). Relatório executivo formalizado em PDF (`outputs/relatorio/relatorio_analise_gt_compras_pb.pdf`).
- **[✓] Qualidade da base de contratos:** deduplicação por contrato (`src/etl/dedup_contratos.py`, chave `registroCge` ou `urlContrato` para contratos do PNCP); aditivos e apostilas já consolidados em `valorTotal`; validação cruzada com a planilha da CAGEPA (`scripts/valida_cagepa_planilha.py`, relatórios em `outputs/validacao_cagepa/`). Base atual: 15.352 contratos únicos.
- **[ ] Auditoria pendente:** `contratacoes` e `itens_contratacoes` (duplicidades) e `dim_contratacoes_macro`.
- **[ ] Próximos Módulos:** Incorporação do PIB municipal e VAB (Valor Adicionado Bruto).

---

## 📜 Licença e Direitos Autorais

Este projeto está sob a licença open-source **MIT License** (consulte o arquivo [LICENSE](LICENSE) para maiores detalhes).

- **Coordenação do Projeto**: Prof. Dr. Paulo Fernando Cavalcanti
- **Desenvolvimento e Colaboração**: Evandro Farias Rocha
- **Instituições parceiras**: UFPB / SUDENE / Governo do Estado da Paraíba

---

## 🤖 Nota de Transparência e Apoio Tecnológico em IA

Este projeto adota boas práticas de integridade e transparência no uso de inteligência artificial. 

> *O desenvolvimento da arquitetura computacional, pipelines de ETL, scripts de raspagem e componentes visuais Streamlit contaram com o auxílio autônomo da ferramenta de **Agentes de IA (Google Gemini Agentic Coding / Antigravity Agentic Framework)** como suporte à programação, refinamento de código e estruturação de bases analíticas.*


