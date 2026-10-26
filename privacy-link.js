/* Carburants et Taxes — pied de page : avertissement « appli non officielle »,
   sources officielles et lien vers la politique de confidentialité.
   Exigé par Google Play (règlement sur les déclarations trompeuses + confidentialité). */
(function () {
  function add() {
    if (document.getElementById('ct-privacy-link')) return;
    var a = 'style="color:inherit;text-decoration:underline;" target="_blank" rel="noopener"';
    var box = document.createElement('div');
    box.id = 'ct-privacy-link';
    box.style.cssText = 'text-align:center;font-size:12px;line-height:1.6;margin:20px 0 8px;color:var(--muted,#5E7268);';
    box.innerHTML =
      '<p style="margin:0 0 8px;"><b>Application indépendante et non officielle</b> : elle n\'est affiliée à aucune ' +
      'administration et ne représente pas le gouvernement français. Les chiffres sont calculés à partir de données publiques.</p>' +
      '<p style="margin:0 0 8px;">Sources officielles : ' +
      '<a href="https://www.prix-carburants.gouv.fr" ' + a + '>prix-carburants.gouv.fr</a> · ' +
      '<a href="https://www.ecologie.gouv.fr/politiques-publiques/prix-produits-petroliers" ' + a + '>ecologie.gouv.fr</a> · ' +
      '<a href="https://data.economie.gouv.fr/explore/dataset/prix-des-carburants-en-france-flux-instantane-v2/" ' + a + '>data.economie.gouv.fr</a> · ' +
      '<a href="https://www.insee.fr" ' + a + '>insee.fr</a></p>' +
      '<p style="margin:0;"><a href="confidentialite.html" style="color:inherit;text-decoration:underline;">Politique de confidentialité</a>' +
      ' · aucune donnée collectée, aucun cookie</p>';
    (document.querySelector('.wrap') || document.body).appendChild(box);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add);
  else add();
})();
