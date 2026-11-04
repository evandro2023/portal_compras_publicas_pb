-- ==============================================================================
-- PROJETO: Portal de Compras Públicas da Paraíba
-- FINALIDADE: Consultas SQL para Análise do Programa Nacional de Alimentação
--             Escolar (PNAE) e Compras de Merenda na Secretaria de Educação (SEE)
-- BANCO DE DADOS: DuckDB (data/compras_pb.duckdb)
-- AUTOR: Grupo de Trabalho (GT) / Antigravity AI
-- DATA: 2026-11-03
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. PLANEJAMENTO ORÇAMENTÁRIO (PCA - PLANO ANUAL DE CONTRATAÇÃO)
-- Identifica as dotações planejadas nas contas orçamentárias de alimentação escolar:
--   - 33903007: Gêneros de Alimentação (Material de Consumo)
--   - 33903941: Fornecimento de Alimentação (Serviços de Terceiros - PJ)
-- ------------------------------------------------------------------------------
SELECT 
    ano_referencia AS ano,
    nomeOrgao AS orgao,
    codigoItem AS codigo_conta,
    classeGrupo AS classificacao_despesa,
    descricaoItem AS item_planejado,
    quantidade,
    valorUnitario AS valor_unitario_estimado,
    valorTotal AS valor_total_planejado
FROM plano_anual_contratacao
WHERE nomeOrgao ILIKE '%EDUCA%'
  AND (
      descricaoItem ILIKE '%MERENDA%' 
      OR descricaoItem ILIKE '%PNAE%' 
      OR descricaoItem ILIKE '%ALIMENTA%' 
      OR descricaoItem ILIKE '%GENERO%'
  )
ORDER BY ano_referencia DESC, valorTotal DESC;


-- ------------------------------------------------------------------------------
-- 2. PROCESSOS LICITATÓRIOS E INSTRUMENTOS DO PNAE (CHAMAMENTO PÚBLICO / PREGÕES)
-- Filtra as licitações e chamadas públicas de merenda com destaque para o amparo
-- legal da Lei 14.628/2023 (marco de aquisições da Agricultura Familiar / PAA / PNAE)
-- ------------------------------------------------------------------------------
SELECT 
    ano_referencia AS ano,
    numeroProcesso,
    numeroLicitacao,
    nomeOrgao,
    modalidade,
    amparoLegal AS amparo_legal,
    objeto,
    valorEstimado AS valor_estimado,
    valorAdjudicado AS valor_adjudicado,
    urlContratacao AS link_edital_ou_processo
FROM contratacoes
WHERE (nomeOrgao ILIKE '%EDUCA%' OR objeto ILIKE '%MERENDA%' OR objeto ILIKE '%ALIMENTAÇÃO ESCOLAR%')
  AND (
      objeto ILIKE '%MERENDA%' 
      OR objeto ILIKE '%PNAE%' 
      OR objeto ILIKE '%ALIMENTA%' 
      OR amparoLegal ILIKE '%14.628%'
      OR amparoLegal ILIKE '%11.947%'
  )
ORDER BY ano_referencia DESC, valorAdjudicado DESC;


-- ------------------------------------------------------------------------------
-- 3. CONTRATOS FIRMADOS DE MERENDA E ALIMENTAÇÃO DA EDUCAÇÃO
-- Traz os contratos celebrados, empresas vencedoras, valores e vigência
-- ------------------------------------------------------------------------------
SELECT 
    c.ano_referencia AS ano,
    c.registroCge,
    c.numeroContrato,
    c.contratado AS razao_social_fornecedor,
    c.cnpjCpf AS cnpj_fornecedor,
    c.dataAssinatura,
    c.dataInicioVigencia,
    c.dataTerminoVigencia,
    c.valorOriginal,
    c.valorAditivos,
    c.valorTotal AS valor_total_contratado,
    c.objeto
FROM contratos c
WHERE c.nomeOrgao ILIKE '%EDUCA%'
  AND (
      c.objeto ILIKE '%MERENDA%' 
      OR c.objeto ILIKE '%ALIMENTA%' 
      OR c.objeto ILIKE '%GENERO%'
  )
ORDER BY c.ano_referencia DESC, c.valorTotal DESC;


-- ------------------------------------------------------------------------------
-- 4. ANÁLISE DE RETENÇÃO TERRITORIAL E PERFIL PRODUTIVO (CNAE E LOCALIZAÇÃO)
-- Cruza os contratos da Educação com o enriquecimento da Receita Federal
-- para responder: Onde está ficando o dinheiro da merenda escolar?
-- ------------------------------------------------------------------------------
SELECT 
    COALESCE(f.localizacao_categoria, 'Não Identificado') AS categoria_geografica,
    COALESCE(f.uf, 'ND') AS uf_fornecedor,
    COALESCE(f.municipio, 'Não Informado') AS municipio_fornecedor,
    COUNT(c.numeroContrato) AS qtd_contratos,
    COUNT(DISTINCT c.cnpjCpf) AS qtd_empresas_distintas,
    SUM(c.valorTotal) AS total_gasto_reais,
    ROUND(SUM(c.valorTotal) * 100.0 / SUM(SUM(c.valorTotal)) OVER (), 2) AS participacao_percentual
FROM contratos c
LEFT JOIN dim_fornecedores_cnae f 
    ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = LPAD(CAST(CAST(f.cnpj AS BIGINT) AS VARCHAR), 14, '0')
WHERE c.nomeOrgao ILIKE '%EDUCA%'
  AND (
      c.objeto ILIKE '%MERENDA%' 
      OR c.objeto ILIKE '%ALIMENTA%' 
      OR c.objeto ILIKE '%GENERO%'
  )
GROUP BY 1, 2, 3
ORDER BY total_gasto_reais DESC;


-- ------------------------------------------------------------------------------
-- 5. DETALHAMENTO DE FORNECEDORES: CNAE, RAMO DE ATUAÇÃO E ORIGEM
-- ------------------------------------------------------------------------------
SELECT 
    c.numeroContrato,
    c.ano_referencia AS ano,
    c.contratado,
    c.cnpjCpf,
    f.uf,
    f.municipio,
    f.localizacao_categoria,
    f.cnae_fiscal,
    f.cnae_descricao,
    f.setor_economico,
    c.valorTotal,
    c.objeto
FROM contratos c
LEFT JOIN dim_fornecedores_cnae f 
    ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = LPAD(CAST(CAST(f.cnpj AS BIGINT) AS VARCHAR), 14, '0')
WHERE c.nomeOrgao ILIKE '%EDUCA%'
  AND (
      c.objeto ILIKE '%MERENDA%' 
      OR c.objeto ILIKE '%ALIMENTA%' 
      OR c.objeto ILIKE '%GENERO%'
  )
ORDER BY c.valorTotal DESC;

