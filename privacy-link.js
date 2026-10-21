/* Carburants et Taxes — lien vers la politique de confidentialité, en bas de page.
   Exigé par Google Play : la politique doit être accessible depuis l'appli elle-même. */
(function () {
  function add() {
    if (document.getElementById('ct-privacy-link')) return;
    var p = document.createElement('p');
    p.id = 'ct-privacy-link';
    p.style.cssText = 'text-align:center;font-size:12px;line-height:1.5;margin:20px 0 8px;color:var(--muted,#5E7268);';
    p.innerHTML = '<a href="confidentialite.html" style="color:inherit;text-decoration:underline;">Politique de confidentialité</a>' +
                  ' · aucune donnée collectée, aucun cookie';
    (document.querySelector('.wrap') || document.body).appendChild(p);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add);
  else add();
})();
