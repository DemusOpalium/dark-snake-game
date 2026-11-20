/* No frameworks, trackers, cookies, network requests or dynamic downloads. */
(() => {
  'use strict';
  const buttons = document.querySelectorAll('[data-language]');
  const supported = ['de', 'en'];
  const descriptions = {
    de: 'DARK SNAKE: kostenloses Windows-Arcade-Snake mit Bosskämpfen, W20-Ereignissen, zwei Spielern und World Studio.',
    en: 'DARK SNAKE: free Windows arcade Snake with bosses, D20 events, two players and World Studio.'
  };
  function setLanguage(lang) {
    if (!supported.includes(lang)) return;
    document.documentElement.lang = lang;
    document.title = lang === 'de' ? 'DARK SNAKE – Kostenloses Indie-Arcade-Spiel' : 'DARK SNAKE – Free Indie Arcade Game';
    document.querySelector('meta[name="description"]').content = descriptions[lang];
    for (const button of buttons) {
      button.setAttribute('aria-pressed', String(button.dataset.language === lang));
    }
    for (const img of document.querySelectorAll('[data-alt-de]')) {
      img.alt = img.getAttribute('data-alt-' + lang);
    }
  }
  for (const button of buttons) {
    button.addEventListener('click', () => setLanguage(button.dataset.language));
  }
  const preferred = (navigator.language || 'de').toLowerCase().startsWith('de') ? 'de' : 'en';
  setLanguage(preferred);
})();
