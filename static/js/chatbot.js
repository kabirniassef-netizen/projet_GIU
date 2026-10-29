// Assistant Typebot : notre bouton s'affiche tout de suite, le script Typebot (~700 Ko)
// n'est téléchargé que lorsque le visiteur s'approche du bouton ou clique dessus.
(() => {
  const root = document.querySelector('.giu-chatbot');
  const configElement = document.getElementById('typebot-config');
  if (!root || !configElement) return;

  const TYPEBOT_SCRIPT = 'https://cdn.jsdelivr.net/npm/@typebot.io/js@0.10.11/dist/web.js';
  // Doit rester égal à --chat-offset + --chat-size + 12 px (chatbot.css) : la fenêtre s'ouvre au-dessus du bouton.
  const WINDOW_BOTTOM = 'calc(88px + env(safe-area-inset-bottom, 0px))';
  const HINT_KEY = 'giu-chatbot-hint-dismissed';

  const config = JSON.parse(configElement.textContent);
  const launcher = root.querySelector('.giu-chatbot-launcher');
  const hint = root.querySelector('.giu-chatbot-hint');
  const status = document.getElementById('giu-chatbot-status');
  let typebotPromise = null;
  let isOpen = false;

  const setOpen = (open) => {
    isOpen = open;
    root.dataset.state = open ? 'open' : 'closed';
    launcher.setAttribute('aria-expanded', String(open));
    launcher.setAttribute('aria-label', open ? 'Fermer l’assistant de signalement' : 'Ouvrir l’assistant de signalement');
    if (open) hideHint(true);
  };

  const loadTypebot = () => {
    typebotPromise ??= import(TYPEBOT_SCRIPT).then(({ default: Typebot }) => {
      Typebot.initBubble({
        typebot: config.typebot,
        apiHost: config.apiHost,
        theme: {
          button: { isHidden: true },
          chatWindow: { maxWidth: '400px', maxHeight: '640px' },
        },
        inlineStyle: { '--container-bottom': WINDOW_BOTTOM },
        onOpen: () => setOpen(true),
        onClose: () => setOpen(false),
      });
      return Typebot;
    });
    typebotPromise.catch(() => { typebotPromise = null; });
    return typebotPromise;
  };

  const toggle = async () => {
    if (isOpen) {
      (await loadTypebot()).close();
      return;
    }
    root.dataset.state = 'loading';
    status.textContent = 'Chargement de l’assistant…';
    try {
      (await loadTypebot()).open();
      status.textContent = '';
    } catch {
      root.dataset.state = 'closed';
      status.textContent = 'L’assistant est indisponible. Utilisez le formulaire de signalement.';
    }
  };

  function hideHint(remember) {
    hint.hidden = true;
    if (!remember) return;
    try { sessionStorage.setItem(HINT_KEY, '1'); } catch { /* stockage indisponible */ }
  }

  launcher.addEventListener('click', toggle);
  // Préchargement dès que le visiteur montre son intention d'ouvrir l'assistant.
  ['pointerenter', 'focus', 'touchstart'].forEach((type) => {
    launcher.addEventListener(type, loadTypebot, { once: true, passive: true });
  });

  hint.querySelector('.giu-chatbot-hint-open').addEventListener('click', toggle);
  hint.querySelector('.giu-chatbot-hint-close').addEventListener('click', () => {
    hideHint(true);
    launcher.focus();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && isOpen) {
      typebotPromise?.then((Typebot) => Typebot.close());
      launcher.focus();
    }
  });

  // La fenêtre de signalement de l'accueil passe devant : on range l'assistant.
  document.addEventListener('show.bs.modal', () => {
    root.dataset.hidden = '';
    if (isOpen) typebotPromise?.then((Typebot) => Typebot.close());
  });
  document.addEventListener('hidden.bs.modal', () => { delete root.dataset.hidden; });

  let hintDismissed = false;
  try { hintDismissed = sessionStorage.getItem(HINT_KEY) === '1'; } catch { /* stockage indisponible */ }
  if (!hintDismissed) {
    setTimeout(() => { if (!isOpen && root.dataset.hidden === undefined) hint.hidden = false; }, 5000);
  }
})();
