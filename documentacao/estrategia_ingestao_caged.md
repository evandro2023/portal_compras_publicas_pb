# Estratégia de Ingestão e Atualização do CAGED (Paraíba)

Este documento detalha a arquitetura de ingestão dos dados econômicos do **Novo CAGED** para a Paraíba (código UF `25`), cobrindo o funcionamento **Local**, a execução **Incremental**, e as orientações para a futura **Migração para Repositoriamento e Nuvem (GitLab / GitHub / CI-CD)**.

---

## 1. Arquitetura Local Atual

Atualmente, os microdados do CAGED são extraídos diretamente dos servidores do Ministério do Trabalho e Emprego (MTE) por meio da biblioteca `pycaged` e consolidados localmente.

### Níveis de Agregação CNAE Suportados
Os dados são agregados por município para os três níveis da classificação CNAE:
- `secao` (Letras A-U)
- `classe` (4 dígitos CNAE - **Essencial para a análise de contratações**)
- `subclasse` (7 dígitos CNAE)

### Estrutura de Arquivos Gerados (Local)
Os dados são armazenados na pasta local (ignorada pelo Git):
- `data/processed/caged/caged_pb_secao_<ANO>.parquet` e `.csv`
- `data/processed/caged/caged_pb_classe_<ANO>.parquet` e `.csv`
- `data/processed/caged/caged_pb_subclasse_<ANO>.parquet` e `.csv`

E carregados no banco de dados analítico local:
- `data/compras_pb.duckdb`

---

## 2. Como Rodar a Atualização na Máquina Local

Para atualizar os dados na sua máquina local de forma rápida e inteligente, utilize a flag `--incremental`:

```bash
# Execução incremental (baixa APENAS os meses do ano que ainda não foram salvos no Parquet local)
PYTHONPATH=. uv run python src/caged/ingest_caged.py --incremental
```

Caso queira forçar a re-ingestão completa de um ano específico:
```bash
PYTHONPATH=. uv run python src/caged/ingest_caged.py --anos 2026 --niveis classe
```

### Agendamento Local via `cron` (Linux)
Para que a sua máquina local busque automaticamente novos meses divulgados pelo MTE no final de cada mês (ex: todo dia 28 às 09:00 AM):

1. Abra o editor de tarefas do Linux:
   ```bash
   crontab -e
   ```
2. Adicione a seguinte linha (substituindo pelo caminho absoluto do seu projeto):
   ```cron
   0 9 28 * * cd /home/sti-gii/Projetos/PythonProject/portal_compras_publica_pb && PYTHONPATH=. .venv/bin/python src/caged/ingest_caged.py --incremental >> data/caged_cron.log 2>&1
   ```

---

## 3. Plano para Migração Futura em Nuvem (GitLab / GitHub CI-CD)

Quando o projeto for implantado em um repositório remoto oficial (GitLab ou GitHub) e hospedado no Streamlit Cloud / Servidor Próprio, siga estas orientações:

### A. Repositório Leve (Boas Práticas de Git)
- **NUNCA** suba os arquivos `.parquet`, `.csv`, `.duckdb` ou `.7z` para o repositório Git. O arquivo `.gitignore` já está configurado para proteger o repositório contra estouro de limite de cota.

### B. Automação via CI/CD (GitLab CI / GitHub Actions)
Quando o repositório remoto estiver ativo, crie um arquivo de pipeline (ex: `.github/workflows/atualiza_caged.yml` ou `.gitlab-ci.yml`):

**Exemplo para GitLab CI (`.gitlab-ci.yml`):**
```yaml
stages:
  - data_sync

atualizar_caged_mensal:
  stage: data_sync
  script:
    - pip install uv
    - uv sync
    - PYTHONPATH=. uv run python src/caged/ingest_caged.py --incremental
  only:
    - schedules # Executa via cron agendado no GitLab CI
```

### C. Armazenamento de Produção (Storage Externo)
Como os servidores de hospedagem como Streamlit Cloud costumam ter discos efêmeros (que apagam ao reiniciar), a estratégia ideal de produção é:
1. O pipeline CI/CD baixa o novo mês do CAGED e gera o `.parquet`.
2. O arquivo `.parquet` compactado é enviado para um repositório de dados/storage (ex: AWS S3, Supabase, Cloudflare R2 ou MinIO).
3. O Streamlit consulta diretamente o Parquet no Storage via DuckDB usando a extensão HTTP:
   ```sql
   SELECT * FROM read_parquet('https://meu-storage.s3.amazonaws.com/caged/caged_pb_classe_2026.parquet');
   ```

---

*Documento gerado em 07/09/2026.*
