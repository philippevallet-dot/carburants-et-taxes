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
import time
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
    "conso_carburant": "011795175",  # Conso des ménages en produits pétroliers raffinés (carburants, fioul), volume CVS-CJO
}

# Séries des comptes trimestriels (base 2020) servant à calculer le taux d'épargne
# et le pouvoir d'achat, avec la même méthode que l'Insee :
#   taux d'épargne = épargne des ménages / (RDB + ajustement pour droits à pension)
#   pouvoir d'achat par UC = évolution du RDB − évolution du prix de la consommation
#                            des ménages − croissance du nombre d'unités de consommation
CNT = {
    "epargne": "011794755",      # Épargne des ménages (y c. EI), prix courants
    "rdb": "011794746",          # Revenu disponible brut des ménages (y c. EI), prix courants
    "ajust": "011794826",        # Ajustement pour variation des droits à pension reçus par les ménages
    "conso_val": "011794863",    # Dépenses de consommation des ménages, prix courants
    "conso_vol": "011794864",    # Dépenses de consommation des ménages, volume
}
CROISSANCE_UC = 0.125  # % par trimestre (≈ +0,5 %/an, croissance du nombre d'unités de consommation)

def get(url, timeout=90, essais=3):
    req = urllib.request.Request(url, headers={"User-Agent": "carburants-et-taxes/1.0"})
    for i in range(essais):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            if i == essais - 1:
                raise
            print("Nouvel essai après erreur :", e)
            time.sleep(20)


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
        if cle in ("defaillances", "conso_carburant"):
            dernier_p, dernier_v = obs[-1]
            # même trimestre un an plus tôt
            a, q = dernier_p.split("-")
            ref = f"{int(a) - 1}-{q}"
            prec = dict(obs).get(ref)
            bilan[cle] = {
                "periode": dernier_p,
                "nombre": int(dernier_v) if cle == "defaillances" else None,
                "evol_an": round((dernier_v / prec - 1) * 100, 1) if prec else None,
            }
        else:
            bilan[cle] = {**point(obs), "precedent": point(obs, -2)}
        print(cle, "→", bilan[cle])

    # 2) Taux d'épargne et pouvoir d'achat par unité de consommation (calculés)
    try:
        cnt = series_from_xml(get(BDM + "SERIES_BDM/" + "+".join(CNT.values()) + "?lastNObservations=4"))
        o = {k: dict(cnt[idb]["obs"]) for k, idb in CNT.items()}
        periodes = sorted(set.intersection(*[set(v) for v in o.values()]))[-3:]
        if len(periodes) < 3:
            raise ValueError("trimestres communs insuffisants")
        ep = {p: o["epargne"][p] / (o["rdb"][p] + o["ajust"][p]) * 100 for p in periodes}
        prix = {p: o["conso_val"][p] / o["conso_vol"][p] for p in periodes}
        pa = {}
        for i in (1, 2):
            p, q = periodes[i], periodes[i - 1]
            pa[p] = ((o["rdb"][p] / o["rdb"][q]) / (prix[p] / prix[q]) - 1) * 100 - CROISSANCE_UC
        p1, p0 = periodes[2], periodes[1]
        bilan["epargne"] = {"periode": p1, "valeur": round(ep[p1], 1),
                            "precedent": {"periode": p0, "valeur": round(ep[p0], 1)}}
        bilan["pouvoir_achat_uc"] = {"periode": p1, "valeur": round(pa[p1], 1),
                                     "precedent": {"periode": p0, "valeur": round(pa[p0], 1)}}
        print("epargne →", bilan["epargne"])
        print("pouvoir_achat_uc →", bilan["pouvoir_achat_uc"])
    except Exception as e:
        print("Épargne / pouvoir d'achat : calcul impossible, valeurs conservées :", e)

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
