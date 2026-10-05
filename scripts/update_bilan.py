#!/usr/bin/env python3
"""Met à jour bilan.json (onglet « Bilan ») à partir des séries publiques de l'Insee.

Lancé chaque jour par .github/workflows/update-bilan.yml : le fichier ne change
(et n'est commité) que lorsque l'Insee publie un nouveau chiffre, c'est-à-dire
au rythme des publications (PIB, pouvoir d'achat, chômage, défaillances).

Aucune clé API nécessaire : la BDM de l'Insee (SDMX) est en accès libre.
Toute série introuvable ou invalide est ignorée : on garde la valeur précédente.
"""
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

BDM = "https://bdm.insee.fr/series/sdmx/data/"
FICHIER = "bilan.json"

# Séries à identifiant fixe (vérifiées)
IDBANK = {
    "pib": "011794844",           # Évolution trimestrielle du PIB en volume (CVS-CJO), en %
    "chomage": "001688527",       # Taux de chômage BIT, France hors Mayotte, CVS, en %
    "defaillances": "001656164",  # Défaillances d'entreprises, données brutes, tous secteurs, par trimestre
}

# Séries repérées par leur intitulé dans le flux des comptes de secteurs (CNT base 2020)
RECHERCHE_CSI = {
    "pouvoir_achat_uc": re.compile(r"pouvoir d.achat.*unit[ée]s? de consommation", re.I),
    "epargne": re.compile(r"taux d.[ée]pargne des m[ée]nages", re.I),
}
EXCLURE = re.compile(r"s[ée]rie arr[êe]t[ée]e|niveau|valeur aux prix|annuel", re.I)


def get(url, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": "carburants-et-taxes/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def series_from_xml(raw):
    """Renvoie {idbank: {"titre": str, "obs": [(periode, valeur), ...] triées}}."""
    out = {}
    root = ET.fromstring(raw)
    for s in root.iter():
        if not s.tag.endswith("Series"):
            continue
        obs = []
        for o in s:
            if not o.tag.endswith("Obs"):
                continue
            p, v = o.get("TIME_PERIOD"), o.get("OBS_VALUE")
            try:
                obs.append((p, float(v)))
            except (TypeError, ValueError):
                pass
        obs.sort()
        out[s.get("IDBANK")] = {"titre": s.get("TITLE_FR", ""), "obs": obs}
    return out


def point(obs, i=-1):
    p, v = obs[i]
    return {"periode": p, "valeur": round(v, 2)}


def main():
    try:
        with open(FICHIER, encoding="utf-8") as f:
            bilan = json.load(f)
    except (OSError, ValueError):
        bilan = {}
    avant = json.dumps(bilan, sort_keys=True)

    # 1) Séries à identifiant fixe
    try:
        raw = get(BDM + "SERIES_BDM/" + "+".join(IDBANK.values()) + "?lastNObservations=6")
        data = series_from_xml(raw)
    except Exception as e:  # réseau, XML invalide…
        print("BDM indisponible :", e)
        data = {}

    for cle, idb in IDBANK.items():
        obs = data.get(idb, {}).get("obs", [])
        if len(obs) < 2:
            print(f"{cle} ({idb}) : pas de données, valeur conservée")
            continue
        if cle == "defaillances":
            dernier_p, dernier_v = obs[-1]
            # même trimestre un an plus tôt
            a, q = dernier_p.split("-")
            ref = f"{int(a) - 1}-{q}"
            prec = dict(obs).get(ref)
            bilan[cle] = {
                "periode": dernier_p,
                "nombre": int(dernier_v),
                "evol_an": round((dernier_v / prec - 1) * 100, 1) if prec else None,
            }
        else:
            bilan[cle] = {**point(obs), "precedent": point(obs, -2)}
        print(cle, "→", bilan[cle])

    # 2) Pouvoir d'achat par UC et taux d'épargne (recherche par intitulé)
    try:
        csi = series_from_xml(get(BDM + "CNT-2020-CSI?lastNObservations=2", timeout=240))
    except Exception as e:
        print("Flux CNT-2020-CSI indisponible :", e)
        csi = {}
    for cle, motif in RECHERCHE_CSI.items():
        cands = [
            (idb, s) for idb, s in csi.items()
            if motif.search(s["titre"]) and not EXCLURE.search(s["titre"]) and len(s["obs"]) >= 2
        ]
        if cle == "pouvoir_achat_uc":
            # on veut l'évolution trimestrielle (valeurs en %, petites)
            cands = [c for c in cands if abs(c[1]["obs"][-1][1]) < 10]
        if not cands:
            print(f"{cle} : série introuvable, valeur conservée")
            continue
        idb, s = sorted(cands, key=lambda c: len(c[1]["titre"]))[0]
        bilan[cle] = {**point(s["obs"]), "precedent": point(s["obs"], -2), "idbank": idb}
        print(cle, "→", idb, s["titre"], bilan[cle])

    # 3) Record du gazole (moyenne nationale), suivi à partir de prix.json
    try:
        with open("prix.json", encoding="utf-8") as f:
            prix = json.load(f)
        g = prix.get("gazole")
        rec = bilan.get("record_gazole") or {}
        if isinstance(g, (int, float)) and 1 < g < 4 and g > rec.get("prix", 0):
            bilan["record_gazole"] = {"prix": g, "date": prix.get("date", "")[:10]}
            print("Nouveau record gazole :", bilan["record_gazole"])
    except (OSError, ValueError):
        pass

    if json.dumps(bilan, sort_keys=True) == avant:
        print("Aucune nouvelle publication.")
        return 0
    bilan["maj"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    bilan["source"] = "Insee (BDM) ; prix à la pompe : data.economie.gouv.fr"
    with open(FICHIER, "w", encoding="utf-8") as f:
        json.dump(bilan, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(open(FICHIER, encoding="utf-8").read())
    return 0


if __name__ == "__main__":
    sys.exit(main())
