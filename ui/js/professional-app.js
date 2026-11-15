/**
 * ui/js/professional-app.js
 * Application controller for LabelLens Professional Workspace.
 * 
 * Hard rules:
 * - Professional device workspace only (21 CFR 801, 820, 830).
 * - Must not import or reference any public module.
 * - All data loading through data.js.
 * - No em dashes.
 */

(function() {
  let activeScreen = 'D4 Inspect';

  function init() {
    setupNav();
    setupScreenListeners();
    switchProfessionalScreen(activeScreen);
  }

  function setupNav() {
    const sidebarLinks = document.querySelectorAll('.sidebar-link[data-screen]');
    sidebarLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const screen = link.dataset.screen;
        switchProfessionalScreen(screen);
      });
    });
  }

  function setupScreenListeners() {
    // Listen for mock state changes dispatched by state-switcher.js
    window.addEventListener('labellens:state-changed', (e) => {
      const { screen, state, meta, data } = e.detail;
      renderProfessionalPayload(screen, state, meta, data);
    });

    // Listen for screen switch initiated from dev state switcher or internal action
    window.addEventListener('labellens:screen-navigated', (e) => {
      const screen = e.detail.screen;
      if (screen && screen.startsWith('D')) {
        switchProfessionalScreen(screen);
      }
    });
  }

  function switchProfessionalScreen(screenName) {
    activeScreen = screenName;

    // Update sidebar active link
    const sidebarLinks = document.querySelectorAll('.sidebar-link[data-screen]');
    sidebarLinks.forEach(link => {
      link.classList.toggle('active', link.dataset.screen === screenName);
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

  function renderProfessionalPayload(screen, state, meta, data) {
    const container = document.getElementById('professionalDynamicContent');
    if (!container) return;

    const renderers = window.LabelLensRenderers || {};
    const renderer = renderers[screen] || renderers[screen.split(' ')[0]];

    if (typeof renderer === 'function') {
      renderer(container, state, meta, data);
    } else {
      console.warn('No professional renderer found for screen:', screen);
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
