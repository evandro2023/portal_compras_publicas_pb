-- ============================================================================
-- 01_resumo_4_grandes_setores_cagepa.sql
-- Descrição: Retorna o resumo consolidado das compras de bens da CAGEPA
-- nos 4 Grandes Setores Econômicos (IBGE/CGCE), separado por origem setorial
-- (Indústria Fabril vs. Comércio Distribuidor), retenção na Paraíba e
-- vazamento para outros estados (2024–2026).
-- Corresponde à Aba 1 ("Resumo_4_Grandes_Setores") e à Tabela 1 do PDF.
-- ============================================================================

WITH fornecedores_cgce AS (
    SELECT 
        cnpj,
        is_paraiba,
        CAST(cnae_fiscal AS BIGINT) AS cnae_fiscal,
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
)
SELECT 
    f.grande_setor_cgce,
    f.origem_setor,
    COUNT(*) AS total_contratos,
    SUM(CASE WHEN f.is_paraiba THEN 1 ELSE 0 END) AS contratos_pb,
    SUM(CASE WHEN NOT f.is_paraiba THEN 1 ELSE 0 END) AS contratos_fora_pb,
    ROUND(SUM(c.valorTotal), 2) AS valor_total,
    ROUND(SUM(CASE WHEN f.is_paraiba THEN c.valorTotal ELSE 0 END), 2) AS valor_pb,
    ROUND(SUM(CASE WHEN NOT f.is_paraiba THEN c.valorTotal ELSE 0 END), 2) AS valor_fora_pb,
    COUNT(DISTINCT f.cnae_fiscal) AS cnaes_distintos,
    ROUND(
        SUM(CASE WHEN NOT f.is_paraiba THEN c.valorTotal ELSE 0 END) * 100.0 / SUM(c.valorTotal), 
        2
    ) AS pct_valor_fora_pb
FROM contratos c
INNER JOIN fornecedores_cgce f 
    ON REGEXP_REPLACE(c.cnpjCpf, '[^0-9]', '', 'g') = LPAD(CAST(CAST(f.cnpj AS BIGINT) AS VARCHAR), 14, '0')
WHERE UPPER(c.siglaOrgao) LIKE '%CAGEPA%'
  AND c.valorTotal IS NOT NULL
  AND f.grande_setor_cgce IS NOT NULL
GROUP BY f.grande_setor_cgce, f.origem_setor
ORDER BY valor_total DESC;

