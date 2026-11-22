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
  let activeScreen = 'P1 Scan and Understand';

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
        switchPublicScreen(screen, null, true);
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
      const state = e.detail.state || null;
      if (screen && screen.startsWith('P')) {
        switchPublicScreen(screen, state);
      }
    });
  }

  function switchPublicScreen(screenName, initialState = null, force = false) {
    const isNewScreen = activeScreen !== screenName;
    activeScreen = screenName;

    // Update public nav tab active classes
    const publicTabs = document.querySelectorAll('.public-nav-btn[data-screen]');
    publicTabs.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.screen === screenName);
    });

    // Notify state switcher to adapt its states for this screen
    if (window.LabelLensStateSwitcher) {
      if (window.LabelLensStateSwitcher.getCurrentScreen() !== screenName || initialState || force) {
        window.LabelLensStateSwitcher.setScreen(screenName, initialState);
      }
    } else {
      window.dispatchEvent(new CustomEvent('labellens:screen-changed', {
        detail: { screen: screenName, state: initialState }
      }));
    }
  }

  /** P2 with nothing loaded: say so, offer the typed lookup (Scan tab) and the live DailyMed search. */
  function renderNoLabel(container) {
    const typed = (window.LabelLensLive && window.LabelLensLive.currentName()) || '';
    container.innerHTML = `
      <div class="card" data-testid="no-label-loaded" style="max-width: 720px; margin: 0 auto; padding: 24px;">
        <h3>No label loaded for this name</h3>
        <p class="text-sm text-muted" style="margin: 8px 0 12px 0;">Scan a pack or type a name on the first tab, or search DailyMed for the label.</p>
        <label class="text-xs text-muted" for="noLabelName">Medicine name</label>
        <input type="text" id="noLabelName" value="${window.LabelLensData.escapeHtml(typed)}" placeholder="for example: Advil" style="width: 100%; padding: 6px 10px; border: 1px solid var(--color-border); border-radius: var(--radius-md);">
        <div id="noLabelLive"></div>
      </div>`;
    if (window.LabelLensLive) {
      window.LabelLensLive.mountSearch(container.querySelector('#noLabelLive'), () => container.querySelector('#noLabelName').value);
    }
  }

  function renderPublicPayload(screen, state, meta, data) {
    const container = document.getElementById('publicDynamicContent');
    if (!container) return;

    const renderers = window.LabelLensRenderers || {};
    const renderer = renderers[screen] || renderers[screen.split(' ')[0]];

    // Api mode never shows sample data: a mock that stands in for a screen with no live answer (marked x-mock)
    // (outside the dev panel) is replaced by "No label loaded" on P2, and by an empty question box on P3.
    const apiMode = window.LabelLensData && window.LabelLensData.CONFIG.mode === 'api';
    const devPanel = new URLSearchParams(location.search).get('dev') === '1'; // the dev panel picks mock states on purpose
    if (apiMode && !devPanel && meta && meta.source === 'x-mock') {
      if (screen.startsWith('P2')) { renderNoLabel(container); return; }
      if (screen.startsWith('P3') && typeof renderer === 'function') { renderer(container, state, meta, null); return; }
    }

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
