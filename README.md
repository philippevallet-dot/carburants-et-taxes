# Carburants et Taxes

Petite appli web (PWA) qui décompose le prix des carburants entre coût réel et taxes, permet de calculer ses pleins, de partager le résultat et de suivre l'impact de la crise pétrolière sur les finances publiques.

## Hébergement (GitHub Pages)

Ce dossier est prêt à être publié tel quel avec GitHub Pages : `index.html` à la racine, `manifest.json` et `sw.js` pour en faire une PWA installable, icônes dans `icons/`.

Une fois en ligne, l'URL GitHub Pages (`https://<utilisateur>.github.io/<repo>/`) peut être utilisée avec [PWABuilder](https://www.pwabuilder.com) pour générer le package Android (Google Play) et, si besoin, le wrapper iOS.

## Mise à jour automatique du cours du Brent

Le fichier `brent.json` (à la racine) contient le dernier cours connu ; l'appli le lit au chargement et bascule dessus si présent (sinon elle garde une valeur de secours codée en dur).

Un workflow GitHub Actions (`.github/workflows/update-brent.yml`) régénère ce fichier chaque jour à 6h UTC, via l'API [OilPriceAPI](https://www.oilpriceapi.com) (plan gratuit largement suffisant : un seul appel/jour).

Pour l'activer :
1. Crée un compte gratuit sur oilpriceapi.com et copie ta clé API.
2. Ajoute-la comme secret du dépôt :
   ```bash
   gh secret set OILPRICE_API_KEY
   ```
   (colle la clé quand demandé), ou via Settings → Secrets and variables → Actions sur github.com.
3. Lance le workflow une première fois pour vérifier que tout fonctionne :
   ```bash
   gh workflow run update-brent.yml
   ```
4. Ensuite, il tourne seul chaque jour — tous les visiteurs de l'appli reçoivent automatiquement le cours à jour.
