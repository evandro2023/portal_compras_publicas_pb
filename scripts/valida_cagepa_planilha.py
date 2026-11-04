"""Validação cruzada: planilha de contratos da CAGEPA x portal (DuckDB) x API.

Gera em outputs/validacao_cagepa/:
  - divergencias_valor_final.csv   contratos casados com valor final diferente
  - planilha_ausentes_no_portal.csv  contratos da planilha que não estão no portal, com retorno da API
  - portal_ausentes_na_planilha.csv  contratos do portal (CAGEPA) que não estão na planilha, com retorno da API

Uso: python scripts/valida_cagepa_planilha.py <api_contratos.pkl>
O .pkl é gerado pela coleta completa de /contratos (anoInicioVigencia 2016-2026).
"""
import re
import sys
import unicodedata
from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "outputs" / "validacao_cagepa"
ORGAO = "COMPANHIA DE ÁGUA E ESGOTOS DO ESTADO DA PARAÍBA"
ANOS = ["2024", "2025", "2026"]


def nm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]", "", s)[:12]


def num_norm(n):
    """'00083/2026' e '0083/2026' -> '83/2026'"""
    n = str(n).strip()
    m = re.match(r"^0*(\d+)/(\d{4})$", n)
    return f"{int(m.group(1))}/{m.group(2)}" if m else n


def carrega_planilha():
    d = pd.read_excel(RAIZ / "documentacao" / "contratos_cagepa.xlsx", sheet_name="Extratos de Contratos")
    d.columns = [" ".join(str(c).split()) for c in d.columns]
    d["tipo"] = d["tipo"].astype(str).str.strip().str.lower()
    for c in ["valor", "valor original", "valor acumulado"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["num"] = d["Nº do contrato"].astype(str).str.strip()
    d["numn"] = d["num"].map(num_norm)
    d["ano"] = d["num"].str[-4:]
    d["nm"] = d["Contratado"].map(nm)
    d["ini"] = pd.to_datetime(d["inicio (vigencia)"], errors="coerce")
    d["Contratado"] = d["Contratado"].astype(str).str.replace("\n", " ")
    return d


def main(api_pkl):
    SAIDA.mkdir(parents=True, exist_ok=True)
    d = carrega_planilha()
    con = duckdb.connect(str(RAIZ / "data" / "compras_pb.duckdb"), read_only=True)
    p = con.execute(
        "select registroCge, numeroContrato num, nomeOrgao, contratado, cnpjCpf, dataAssinatura, "
        "valorOriginal, valorAditivos, valorApostilas, valorTotal, ano_referencia from contratos"
    ).df()
    p["numn"] = p["num"].map(num_norm)
    p["nm"] = p["contratado"].map(nm)
    pc = p[p["nomeOrgao"].str.startswith("COMPANHIA DE ÁGUA", na=False)]

    k = d[(d.tipo == "contrato") & d.ano.isin(ANOS)].drop_duplicates(["numn", "nm"])
    a = d[d.ano.isin(ANOS)].sort_values(["numn", "nm", "ini"]).dropna(subset=["valor acumulado"])
    ult = a.groupby(["numn", "nm"]).tail(1)[["numn", "nm", "valor acumulado"]].rename(
        columns={"valor acumulado": "valor_final_planilha"})
    adit = d[d.ano.isin(ANOS) & (d.tipo != "contrato")].drop_duplicates(["numn", "nm", "tipo", "valor", "ini"])
    soma_adit = adit.groupby(["numn", "nm"])["valor"].sum().rename("soma_aditivos_planilha").reset_index()
    qtd_adit = adit.groupby(["numn", "nm"]).size().rename("qtd_linhas_aditivo_planilha").reset_index()

    # ---------- 1) divergências de valor final ----------
    b = (k.merge(pc, on=["numn", "nm"], suffixes=("", "_p"))
          .merge(ult, on=["numn", "nm"], how="left")
          .merge(soma_adit, on=["numn", "nm"], how="left")
          .merge(qtd_adit, on=["numn", "nm"], how="left"))
    b["valor_final_planilha"] = b["valor_final_planilha"].fillna(b["valor original"])
    b["diferenca_portal_menos_planilha"] = (b["valorTotal"] - b["valor_final_planilha"]).round(2)
    div = b[b["diferenca_portal_menos_planilha"].abs() >= 1].copy()
    div["diferenca_pct"] = (div["diferenca_portal_menos_planilha"] / div["valor_final_planilha"] * 100).round(2)

    def motivo(r):
        if r["diferenca_portal_menos_planilha"] > 0:
            return "Portal/API registra aditivos/apostilas não refletidos no valor acumulado da planilha"
        return "Planilha com valor acumulado maior que o portal/API"
    div["motivo_provavel"] = div.apply(motivo, axis=1)
    cols = {
        "num": "numero_contrato", "Contratado": "contratado_planilha", "nomeOrgao": "orgao_portal",
        "registroCge": "registro_cge", "valor original": "valor_original_planilha",
        "valorOriginal": "valor_original_portal", "valorAditivos": "valor_aditivos_portal",
        "valorApostilas": "valor_apostilas_portal", "valorTotal": "valor_total_portal",
        "soma_aditivos_planilha": "soma_aditivos_planilha",
        "qtd_linhas_aditivo_planilha": "qtd_linhas_aditivo_planilha",
        "valor_final_planilha": "valor_final_planilha",
        "diferenca_portal_menos_planilha": "diferenca_portal_menos_planilha",
        "diferenca_pct": "diferenca_pct", "motivo_provavel": "motivo_provavel",
        "link": "link_planilha",
    }
    out = div[list(cols)].rename(columns=cols).sort_values("diferenca_portal_menos_planilha", key=abs, ascending=False)
    out.to_csv(SAIDA / "divergencias_valor_final.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print(f"divergencias: {len(out)} | contratos casados: {len(b)}")

    # ---------- API ----------
    api = pd.read_pickle(api_pkl)
    api["numn"] = api["numeroContrato"].map(num_norm)
    api["nm"] = api["contratado"].map(nm)
    api["orgao_cagepa"] = api["nomeOrgao"].astype(str).str.upper().str.contains("COMPANHIA DE ÁGUA E ESGOTOS", na=False)
    api = api.drop_duplicates(subset=["registroCge", "urlContrato", "numeroContrato", "valorTotal"])
    apic = api[api.orgao_cagepa]
    print("API CAGEPA:", len(apic), apic.groupby("anoInicioVigencia").size().to_dict())

    # Enriquece divergências com o valor atual retornado pela API
    api_val = apic.drop_duplicates("registroCge").set_index("registroCge")["valorTotal"]
    out["valor_total_api_atual"] = out["registro_cge"].map(api_val)
    out["api_confere_com_portal"] = (out["valor_total_api_atual"] - out["valor_total_portal"]).abs() < 1
    out["api_confere_com_planilha"] = (out["valor_total_api_atual"] - out["valor_final_planilha"]).abs() < 1
    out.to_csv(SAIDA / "divergencias_valor_final.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print("divergências em que a API confirma o portal:", int(out.api_confere_com_portal.sum()),
          "| confirma a planilha:", int(out.api_confere_com_planilha.sum()))

    # ---------- 2) planilha -> ausentes no portal, com retorno da API ----------
    chave_portal = set(zip(pc.numn, pc.nm))
    au = k[[(r.numn, r.nm) not in chave_portal for r in k.itertuples()]].copy()
    ap_idx = apic.drop_duplicates(["numn", "nm"]).set_index(["numn", "nm"])
    ap_todos = api.drop_duplicates(["numn", "nm"]).set_index(["numn", "nm"])
    p_todos = set(zip(p.numn, p.nm))

    def api_status(r):
        key = (r.numn, r.nm)
        if key in ap_idx.index:
            x = ap_idx.loc[key]
            return pd.Series({"na_api": "SIM (órgão CAGEPA)", "api_registroCge": x["registroCge"],
                              "api_valorOriginal": x["valorOriginal"], "api_valorTotal": x["valorTotal"],
                              "api_anoInicioVigencia": x["anoInicioVigencia"], "api_dataAssinatura": x["dataAssinatura"],
                              "api_url": x["urlContrato"], "no_portal_outro_orgao": key in p_todos})
        if key in ap_todos.index:
            x = ap_todos.loc[key]
            return pd.Series({"na_api": f"SIM (outro órgão: {x['nomeOrgao']})", "api_registroCge": x["registroCge"],
                              "api_valorOriginal": x["valorOriginal"], "api_valorTotal": x["valorTotal"],
                              "api_anoInicioVigencia": x["anoInicioVigencia"], "api_dataAssinatura": x["dataAssinatura"],
                              "api_url": x["urlContrato"], "no_portal_outro_orgao": key in p_todos})
        return pd.Series({"na_api": "NÃO", "no_portal_outro_orgao": key in p_todos})

    st = au.apply(api_status, axis=1)
    res = pd.concat([au[["num", "Contratado", "valor original", "inicio (vigencia)", "link"]], st], axis=1)
    res = res.rename(columns={"num": "numero_contrato", "Contratado": "contratado_planilha",
                              "valor original": "valor_original_planilha", "inicio (vigencia)": "inicio_vigencia_planilha",
                              "link": "link_planilha"})
    res.to_csv(SAIDA / "planilha_ausentes_no_portal.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print("planilha ausentes no portal:", len(res)); print(res.na_api.str[:10].value_counts().to_string())

    # ---------- 3) portal -> ausentes na planilha, com retorno da API ----------
    chave_plan = set(zip(d.numn, d.nm))
    pa = pc[(pc.ano_referencia.astype(str).isin(ANOS)) &
            pd.Series([(r.numn, r.nm) not in chave_plan for r in pc.itertuples()], index=pc.index)].copy()
    pa["na_api_cagepa"] = [(r.numn, r.nm) in ap_idx.index for r in pa.itertuples()]
    pa["api_valorTotal"] = [ap_idx.loc[(r.numn, r.nm), "valorTotal"] if (r.numn, r.nm) in ap_idx.index else None
                            for r in pa.itertuples()]
    pa["api_url"] = [ap_idx.loc[(r.numn, r.nm), "urlContrato"] if (r.numn, r.nm) in ap_idx.index else None
                     for r in pa.itertuples()]
    pa["confere_com_api"] = (pa["api_valorTotal"] - pa["valorTotal"]).abs() < 1
    pa = pa.drop(columns=["numn", "nm"]).sort_values("valorTotal", ascending=False)
    pa.to_csv(SAIDA / "portal_ausentes_na_planilha.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print("portal ausentes na planilha:", len(pa), "| na API:", int(pa.na_api_cagepa.sum()),
          "| confere valor:", int(pa.confere_com_api.sum()))

    # ---------- 4) API (CAGEPA, 2024-26) -> ausentes no portal ----------
    a2 = apic[apic.anoInicioVigencia.isin([2024, 2025, 2026])].drop_duplicates("registroCge")
    novos = a2[~a2.registroCge.isin(set(pc.registroCge.dropna()))]
    novos[["registroCge", "numeroContrato", "nomeOrgao", "contratado", "cnpjCpf", "dataAssinatura",
           "valorOriginal", "valorAditivos", "valorApostilas", "valorTotal", "urlContrato"]].to_csv(
        SAIDA / "api_ausentes_no_portal.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    print("API ausentes no portal:", len(novos), "| valor:", round(novos.valorTotal.sum(), 2))


if __name__ == "__main__":
    main(sys.argv[1])

