-- ============================================================================
-- 03_fornecedores_pb_potenciais.sql
-- Descrição: Diretório das empresas sediadas na Paraíba (uf = 'PB') que
-- possuem CNAE igual ou próximo (Classe, Grupo ou Divisão) às demandas de
-- bens da CAGEPA nos 4 Grandes Setores Econômicos, indicando se já fornecem
-- ou são potenciais novos fornecedores para adequação/diversificação.
-- Corresponde à Aba 3 ("Fornecedores_PB_Potenciais") e à Tabela 3 do PDF.
-- ============================================================================

WITH fornecedores_cgce AS (
    SELECT 
        LPAD(CAST(CAST(cnpj AS BIGINT) AS VARCHAR), 14, '0') AS cnpj_clean,
        razao_social,
        nome_fantasia,
        uf,
        municipio,
        porte,
        CAST(cnae_fiscal AS BIGINT) AS cnae_fiscal,
        cnae_descricao,
        intensidade_tecnologica,
        CAST(FLOOR(cnae_fiscal / 100000) AS INT) AS divisao,
        CAST(FLOOR(cnae_fiscal / 10000) AS INT) AS grupo,
        CAST(FLOOR(cnae_fiscal / 1000) AS INT) AS classe,
        CASE
            WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 28
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 26 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (261, 262, 265))
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 27 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (271, 273, 279))
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (292, 293))
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 30 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (301, 303, 304, 305))
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 325)
                 OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 33
                 OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (451, 465, 466)
                 THEN 'Bens de Capital'
            WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) BETWEEN 5 AND 9
                 OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) IN (16, 17, 22, 23, 24, 25)
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 20 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) NOT IN (206, 207))
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 294)
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 13 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (131, 132, 133))
                 OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (453, 467, 468)
                 OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 474
                 THEN 'Bens Intermediários'
            WHEN (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 26 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (263, 264, 266, 267, 268))
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 27 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (272, 274, 275))
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 29 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 291)
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 30 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (302, 309))
                 OR CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 31
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) NOT IN (325, 329))
                 OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (452, 454, 475)
                 THEN 'Bens de Consumo Duráveis'
            WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) IN (10, 11, 12, 14, 15, 18, 21)
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 13 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (134, 135))
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 20 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (206, 207))
                 OR (CAST(FLOOR(cnae_fiscal / 100000) AS INT) = 32 AND CAST(FLOOR(cnae_fiscal / 10000) AS INT) = 329)
                 OR CAST(FLOOR(cnae_fiscal / 10000) AS INT) IN (462, 463, 464, 471, 472, 473, 476, 477, 478)
                 THEN 'Bens de Consumo Semiduráveis e Não Duráveis'
            ELSE NULL
        END AS grande_setor_cgce,
        CASE
            WHEN CAST(FLOOR(cnae_fiscal / 100000) AS INT) BETWEEN 5 AND 33 THEN 'Indústria (Fabril)'
            ELSE 'Comércio Distribuidor'
        END AS origem_setor
    FROM dim_fornecedores_cnae
),
contratos_cagepa AS (
    SELECT 
        REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') AS cnpj_vencedor,
        c.valorTotal,
        f.cnae_fiscal,
        f.classe,
        f.grupo,
        f.divisao
    FROM contratos c
    INNER JOIN fornecedores_cgce f 
        ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = f.cnpj_clean
    WHERE UPPER(c.siglaOrgao) LIKE '%CAGEPA%'
      AND c.valorTotal IS NOT NULL
      AND f.grande_setor_cgce IS NOT NULL
),
demanda_cnae AS (SELECT cnae_fiscal, COUNT(*) AS qtd, SUM(valorTotal) AS val FROM contratos_cagepa GROUP BY 1),
demanda_classe AS (SELECT classe, COUNT(*) AS qtd, SUM(valorTotal) AS val FROM contratos_cagepa GROUP BY 1),
demanda_grupo AS (SELECT grupo, COUNT(*) AS qtd, SUM(valorTotal) AS val FROM contratos_cagepa GROUP BY 1),
demanda_divisao AS (SELECT divisao, COUNT(*) AS qtd, SUM(valorTotal) AS val FROM contratos_cagepa GROUP BY 1),
vencedores_cagepa AS (SELECT DISTINCT cnpj_vencedor FROM contratos_cagepa)
SELECT 
    p.cnpj_clean AS cnpj_pb,
    p.razao_social AS razao_social_pb,
    p.nome_fantasia AS nome_fantasia_pb,
    p.municipio AS municipio_pb,
    COALESCE(p.porte, 'N/D') AS porte_pb,
    p.cnae_fiscal AS cnae_fiscal_pb,
    p.cnae_descricao AS cnae_descricao_pb,
    p.grande_setor_cgce,
    p.origem_setor,
    COALESCE(p.intensidade_tecnologica, 'Não Classificado') AS intensidade_tecnologica,
    CASE 
        WHEN dc.cnae_fiscal IS NOT NULL THEN '1. CNAE Exato (Subclasse 7 dígitos)'
        WHEN dcl.classe IS NOT NULL THEN '2. CNAE Próximo (Mesma Classe 4 dígitos)'
        WHEN dgr.grupo IS NOT NULL THEN '3. CNAE Próximo (Mesmo Grupo 3 dígitos)'
        ELSE '4. CNAE Próximo (Mesma Divisão 2 dígitos)'
    END AS grau_proximidade_cagepa,
    CASE WHEN v.cnpj_vencedor IS NOT NULL THEN 'Sim' ELSE 'Não (Potencial Novo Fornecedor)' END AS ja_forneceu_para_cagepa,
    COALESCE(dc.qtd, dcl.qtd, dgr.qtd, ddv.qtd) AS qtd_contratos_cagepa_relacionados,
    ROUND(COALESCE(dc.val, dcl.val, dgr.val, ddv.val), 2) AS valor_demanda_cagepa_relacionada
FROM fornecedores_cgce p
LEFT JOIN demanda_cnae dc ON p.cnae_fiscal = dc.cnae_fiscal
LEFT JOIN demanda_classe dcl ON p.classe = dcl.classe
LEFT JOIN demanda_grupo dgr ON p.grupo = dgr.grupo
LEFT JOIN demanda_divisao ddv ON p.divisao = ddv.divisao
LEFT JOIN vencedores_cagepa v ON p.cnpj_clean = v.cnpj_vencedor
WHERE p.uf = 'PB'
  AND p.cnae_fiscal IS NOT NULL
  AND COALESCE(dc.cnae_fiscal, dcl.classe, dgr.grupo, ddv.divisao) IS NOT NULL
ORDER BY grau_proximidade_cagepa ASC, valor_demanda_cagepa_relacionada DESC, razao_social_pb ASC;

