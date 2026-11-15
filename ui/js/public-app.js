/**
 * ui/js/public-app.js
 * Application controller for LabelLens Public Medicine Mode.
 * 
 * Hard rules:
 * - Public medicine mode only (21 CFR 201, 208, 211).
 * - Must not import or reference any professional module.
 * - All data loading through data.js.
 * - No em dashes.
 */

(function() {
  let activeScreen = 'P2 Product information';

  function init() {
    setupNav();
    setupScreenListeners();
    switchPublicScreen(activeScreen);
  }

  function setupNav() {
    const publicTabs = document.querySelectorAll('.public-nav-btn[data-screen]');
    publicTabs.forEach(btn => {
      btn.addEventListener('click', () => {
        const screen = btn.dataset.screen;
        switchPublicScreen(screen);
      });
    });
  }

  function setupScreenListeners() {
    // Listen for mock state changes dispatched by state-switcher.js
    window.addEventListener('labellens:state-changed', (e) => {
      const { screen, state, meta, data } = e.detail;
      renderPublicPayload(screen, state, meta, data);
    });

    // Listen for screen switch initiated from dev state switcher or internal action
    window.addEventListener('labellens:screen-navigated', (e) => {
      const screen = e.detail.screen;
      if (screen && screen.startsWith('P')) {
        switchPublicScreen(screen);
      }
    });
  }

  function switchPublicScreen(screenName) {
    activeScreen = screenName;

    // Update public nav tab active classes
    const publicTabs = document.querySelectorAll('.public-nav-btn[data-screen]');
    publicTabs.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.screen === screenName);
    });

    // Notify state switcher to adapt its states for this screen
    if (window.LabelLensStateSwitcher) {
      window.LabelLensStateSwitcher.setScreen(screenName);
    } else {
      window.dispatchEvent(new CustomEvent('labellens:screen-changed', {
        detail: { screen: screenName }
      }));
    }
  }

  function renderPublicPayload(screen, state, meta, data) {
    const container = document.getElementById('publicDynamicContent');
    if (!container) return;

    const renderers = window.LabelLensRenderers || {};
    const renderer = renderers[screen] || renderers[screen.split(' ')[0]];

    if (typeof renderer === 'function') {
      renderer(container, state, meta, data);
    } else {
      console.warn('No public renderer found for screen:', screen);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 32px;">
          <h3>${window.LabelLensData ? window.LabelLensData.escapeHtml(screen) : screen}</h3>
          <p class="text-muted text-sm">Renderer not loaded for this screen.</p>
        </div>
      `;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
