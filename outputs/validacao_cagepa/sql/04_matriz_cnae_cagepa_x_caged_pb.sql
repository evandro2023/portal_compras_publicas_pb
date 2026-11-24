-- ============================================================================
-- 04_matriz_cnae_cagepa_x_caged_pb.sql
-- Descrição: Matriz analítica agregada por código CNAE demandado pela CAGEPA
-- nos 4 Grandes Setores Econômicos, cruzando o volume comprado com a quantidade
-- de empresas sediadas na Paraíba e as admissões formais registradas pelo
-- CAGED-PB (2025–2026) na respectiva Subclasse e Divisão CNAE.
-- Corresponde à Aba 4 ("Matriz_CNAE_CAGEPA_x_CAGED") e à Tabela 2 do PDF.
-- ============================================================================

WITH fornecedores_cgce AS (
    SELECT 
        LPAD(CAST(CAST(cnpj AS BIGINT) AS VARCHAR), 14, '0') AS cnpj_clean,
        uf,
        is_paraiba,
        CAST(cnae_fiscal AS BIGINT) AS cnae_fiscal,
        cnae_descricao,
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
empresas_pb AS (
    SELECT * FROM fornecedores_cgce WHERE uf = 'PB' AND cnae_fiscal IS NOT NULL
),
caged_subclasse AS (
    SELECT 
        CAST(LPAD(CAST("CNAE 2.0 Subclas" AS VARCHAR), 7, '0') AS BIGINT) AS cnae_fiscal,
        SUM(CASE WHEN saldo > 0 THEN 1 ELSE 0 END) AS adm_caged_subclasse_25_26
    FROM (
        SELECT "CNAE 2.0 Subclas", saldo FROM caged_pb_subclasse_2025
        UNION ALL
        SELECT "CNAE 2.0 Subclas", saldo FROM caged_pb_subclasse_2026
    )
    GROUP BY 1
),
caged_divisao AS (
    SELECT 
        CAST(SUBSTR(LPAD(CAST("CNAE 2.0 Subclas" AS VARCHAR), 7, '0'), 1, 2) AS INT) AS divisao,
        SUM(CASE WHEN saldo > 0 THEN 1 ELSE 0 END) AS adm_caged_divisao_25_26,
        COUNT(DISTINCT "Município") AS municipios_caged_divisao
    FROM (
        SELECT "CNAE 2.0 Subclas", "Município", saldo FROM caged_pb_subclasse_2025
        UNION ALL
        SELECT "CNAE 2.0 Subclas", "Município", saldo FROM caged_pb_subclasse_2026
    )
    GROUP BY 1
)
SELECT 
    f.grande_setor_cgce,
    f.origem_setor,
    f.cnae_fiscal AS cnae_contratado,
    f.cnae_descricao AS cnae_descricao_contratado,
    f.divisao,
    COUNT(*) AS contratos_cagepa,
    SUM(CASE WHEN f.is_paraiba THEN 1 ELSE 0 END) AS contratos_pb,
    SUM(CASE WHEN NOT f.is_paraiba THEN 1 ELSE 0 END) AS contratos_fora_pb,
    ROUND(SUM(c.valorTotal), 2) AS valor_total_cagepa,
    (SELECT COUNT(*) FROM empresas_pb p WHERE p.cnae_fiscal = f.cnae_fiscal) AS empresas_pb_cnae_exato,
    (SELECT COUNT(*) FROM empresas_pb p WHERE p.classe = f.classe) AS empresas_pb_mesma_classe,
    (SELECT COUNT(*) FROM empresas_pb p WHERE p.grupo = f.grupo) AS empresas_pb_mesmo_grupo,
    (SELECT COUNT(*) FROM empresas_pb p WHERE p.divisao = f.divisao) AS empresas_pb_mesma_divisao,
    COALESCE(MAX(cs.adm_caged_subclasse_25_26), 0) AS caged_pb_admissoes_subclasse_25_26,
    COALESCE(MAX(cd.adm_caged_divisao_25_26), 0) AS caged_pb_admissoes_divisao_25_26,
    COALESCE(MAX(cd.municipios_caged_divisao), 0) AS caged_pb_municipios_ativos_divisao
FROM contratos c
INNER JOIN fornecedores_cgce f 
    ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = f.cnpj_clean
LEFT JOIN caged_subclasse cs ON f.cnae_fiscal = cs.cnae_fiscal
LEFT JOIN caged_divisao cd ON f.divisao = cd.divisao
WHERE UPPER(c.siglaOrgao) LIKE '%CAGEPA%'
  AND c.valorTotal IS NOT NULL
  AND f.grande_setor_cgce IS NOT NULL
GROUP BY f.grande_setor_cgce, f.origem_setor, f.cnae_fiscal, f.cnae_descricao, f.divisao, f.classe, f.grupo
ORDER BY valor_total_cagepa DESC;

