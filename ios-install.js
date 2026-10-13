/* Carburants et Taxes — bandeau d'installation pour iPhone / iPad.
   Safari sur iOS ne propose pas tout seul d'installer une appli web :
   ce bandeau explique la manipulation (Partager → Sur l'écran d'accueil).
   Il ne s'affiche que sur iPhone/iPad, si l'appli n'est pas déjà installée,
   et plus jamais une fois fermé (mémorisé sur l'appareil uniquement). */
(function () {
  var KEY = 'ct_ios_install_ferme';

  var ua = navigator.userAgent || '';
  var isIOS = /iPhone|iPad|iPod/.test(ua) ||
              (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1); // iPadOS se présente comme un Mac
  var installed = window.navigator.standalone === true ||
                  (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches);
  if (!isIOS || installed) return;
  var device = /iPhone|iPod/.test(ua) ? 'iPhone' : 'iPad';

  try { if (localStorage.getItem(KEY)) return; } catch (e) {}

  var css =
    '.ct-ios{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:30;' +
    'max-width:520px;margin:0 auto;background:var(--surface,#fff);color:var(--ink,#142420);' +
    'border:1px solid var(--border,#DCE6DE);border-radius:16px;padding:14px 40px 14px 14px;' +
    'box-shadow:0 8px 28px rgba(0,0,0,.22);font-size:14px;line-height:1.45;display:flex;gap:12px;align-items:flex-start;' +
    'transform:translateY(140%);transition:transform .35s ease;}' +
    '.ct-ios.show{transform:none;}' +
    '.ct-ios img{width:40px;height:40px;border-radius:9px;flex-shrink:0;}' +
    '.ct-ios b{display:block;margin-bottom:2px;}' +
    '.ct-ios svg{width:17px;height:17px;vertical-align:-3px;margin:0 2px;color:var(--cost,#1E7A5F);}' +
    '.ct-ios .ct-x{position:absolute;top:6px;right:6px;width:32px;height:32px;border:0;background:transparent;' +
    'color:var(--muted,#5E7268);font-size:22px;line-height:1;cursor:pointer;border-radius:8px;}';

  var shareIcon =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
    'stroke-linejoin="round" aria-hidden="true"><path d="M12 15V3"/><path d="M8 7l4-4 4 4"/>' +
    '<path d="M6 11H5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-8a1 1 0 0 0-1-1h-1"/></svg>';

  function show() {
    var style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);

    var box = document.createElement('div');
    box.className = 'ct-ios';
    box.setAttribute('role', 'region');
    box.setAttribute('aria-label', "Installer l'appli");
    box.innerHTML =
      '<img src="icons/apple-touch-icon.png" alt="">' +
      '<div><b>Installez l\'appli sur votre ' + device + '</b>' +
      'Touchez ' + shareIcon + ' <b style="display:inline">Partager</b>, puis ' +
      '« <b style="display:inline">Sur l\'écran d\'accueil</b> ».</div>' +
      '<button class="ct-x" type="button" aria-label="Fermer">×</button>';
    document.body.appendChild(box);

    box.querySelector('.ct-x').addEventListener('click', function () {
      box.classList.remove('show');
      try { localStorage.setItem(KEY, '1'); } catch (e) {}
      setTimeout(function () { box.remove(); }, 400);
    });

    requestAnimationFrame(function () { requestAnimationFrame(function () { box.classList.add('show'); }); });
  }

  function start() { setTimeout(show, 1500); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
