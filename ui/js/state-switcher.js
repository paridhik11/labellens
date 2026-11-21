/**
 * ui/js/state-switcher.js
 * Floating developer panel for LabelLens UI.
 * 
 * Hard rules:
 * - Only shows the states that exist for the current screen (dynamically queried from mock index).
 * - Fires 'labellens:state-changed' when a state is selected.
 * - Listens for 'labellens:screen-changed' to update its available state buttons.
 * - Respects module separation: public page only shows public screens, professional page only shows professional screens.
 * - No em dashes.
 */

(function() {
  // Detect module mode from body attribute or URL path
  const isPublicMode = document.body && (document.body.dataset.module === 'public' || window.location.pathname.includes('/public/'));
  const isProfessionalMode = document.body && (document.body.dataset.module === 'professional' || window.location.pathname.includes('/professional/'));

  let currentScreen = isPublicMode ? 'P2 Product information' : 'D4 Inspect';
  let currentState = isPublicMode ? 'success' : 'failed_check';
  // The panel always runs (it loads the mock state that the screens render), but it is only
  // visible with ?dev=1, and starts collapsed. ?dev=1&devopen=1 starts it open (check scripts).
  const urlParams = new URLSearchParams(window.location.search);
  const devVisible = urlParams.get('dev') === '1';
  let isCollapsed = urlParams.get('devopen') !== '1';

  const panelContainer = document.createElement('div');
  panelContainer.className = 'dev-state-panel';
  panelContainer.id = 'devStateSwitcher';
  if (!devVisible) panelContainer.hidden = true;

  function collapseLabel() {
    return isCollapsed ? 'Expand' : 'Collapse';
  }

  function getScreenOptionsHtml() {
    if (isPublicMode) {
      return `
        <optgroup label="Public Medicine Screens">
          <option value="P1 Scan and Understand">P1 Scan and Understand</option>
          <option value="P2 Product information" selected>P2 Product information</option>
          <option value="P3 Ask about this label">P3 Ask about this label</option>
        </optgroup>
      `;
    }

    if (isProfessionalMode) {
      return `
        <optgroup label="Professional Device Screens">
          <option value="D1 Products">D1 Products</option>
          <option value="D2 Template setup">D2 Template setup</option>
          <option value="D3 Upload or scan">D3 Upload or scan</option>
          <option value="D4 Inspect" selected>D4 Inspect</option>
          <option value="D5 Evidence">D5 Evidence</option>
          <option value="D6 Changes">D6 Changes</option>
          <option value="D7 Review">D7 Review</option>
          <option value="D8 Export">D8 Export</option>
          <option value="D9 History">D9 History</option>
          <option value="D10 Print verification">D10 Print verification</option>
        </optgroup>
      `;
    }

    // Default fallback if not scoped to a specific module
    return `
      <optgroup label="Public Medicine Screens">
        <option value="P1 Scan and Understand">P1 Scan and Understand</option>
        <option value="P2 Product information">P2 Product information</option>
        <option value="P3 Ask about this label">P3 Ask about this label</option>
      </optgroup>
      <optgroup label="Professional Device Screens">
        <option value="D1 Products">D1 Products</option>
        <option value="D2 Template setup">D2 Template setup</option>
        <option value="D3 Upload or scan">D3 Upload or scan</option>
        <option value="D4 Inspect" selected>D4 Inspect</option>
        <option value="D5 Evidence">D5 Evidence</option>
        <option value="D6 Changes">D6 Changes</option>
        <option value="D7 Review">D7 Review</option>
        <option value="D8 Export">D8 Export</option>
        <option value="D9 History">D9 History</option>
        <option value="D10 Print verification">D10 Print verification</option>
      </optgroup>
    `;
  }

  function renderPanel() {
    panelContainer.innerHTML = `
      <div class="dev-panel-header" id="devPanelToggle">
        <div class="dev-panel-title">
          <span>Dev State Switcher</span>
          <span class="badge badge-teal text-xs" id="devCurrentScreenBadge">${escapeHtml(currentScreen)}</span>
        </div>
        <div style="font-size: 0.8rem;" id="devCollapseIcon">${collapseLabel()}</div>
      </div>
      <div class="dev-panel-body ${isCollapsed ? 'collapsed' : ''}" id="devPanelBody">
        <div class="flex-between" style="margin-bottom: 6px;">
          <span class="text-xs font-semibold text-muted">Screen:</span>
          <select id="devScreenSelect" style="font-size: 0.78rem; padding: 2px 6px; border-radius: var(--radius-sm); border: 1px solid var(--color-border);">
            ${getScreenOptionsHtml()}
          </select>
        </div>

        <div style="margin-top: 10px;">
          <div class="flex-between">
            <span class="text-xs font-semibold text-muted">States for this screen:</span>
            <span class="text-xs text-muted" id="devStateCount">Loading...</span>
          </div>
          <div class="dev-state-buttons" id="devStateButtons">
            <!-- Dynamically populated buttons -->
          </div>
        </div>

        <div style="margin-top: 10px;">
          <span class="text-xs font-semibold text-muted">Active Mock Contract:</span>
          <div class="dev-meta-box" id="devMetaBox">
            Select a state to inspect payload metadata.
          </div>
        </div>
      </div>
    `;

    // Bind event handlers
    const toggleBtn = panelContainer.querySelector('#devPanelToggle');
    const body = panelContainer.querySelector('#devPanelBody');
    const collapseIcon = panelContainer.querySelector('#devCollapseIcon');

    toggleBtn.addEventListener('click', () => {
      isCollapsed = !isCollapsed;
      body.classList.toggle('collapsed', isCollapsed);
      collapseIcon.textContent = collapseLabel();
    });

    const screenSelect = panelContainer.querySelector('#devScreenSelect');
    screenSelect.value = currentScreen;
    screenSelect.addEventListener('change', (e) => {
      setScreen(e.target.value);
    });
  }

  /**
   * Populate state buttons strictly for the current screen.
   */
  async function refreshStates() {
    const buttonsContainer = panelContainer.querySelector('#devStateButtons');
    const countBadge = panelContainer.querySelector('#devStateCount');
    const screenBadge = panelContainer.querySelector('#devCurrentScreenBadge');
    const screenSelect = panelContainer.querySelector('#devScreenSelect');

    if (screenBadge) screenBadge.textContent = currentScreen;
    if (screenSelect) screenSelect.value = currentScreen;

    if (!buttonsContainer) return;

    buttonsContainer.innerHTML = '<span class="text-xs text-muted">Fetching states...</span>';

    try {
      if (!window.LabelLensData) {
        throw new Error('LabelLensData not loaded yet.');
      }

      const availableStates = await window.LabelLensData.getStatesForScreen(currentScreen);
      countBadge.textContent = `${availableStates.length} state${availableStates.length === 1 ? '' : 's'}`;
      buttonsContainer.innerHTML = '';

      if (availableStates.length === 0) {
        buttonsContainer.innerHTML = '<span class="text-xs text-muted">No states defined for this screen in index.json</span>';
        return;
      }

      availableStates.forEach((item, index) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn-state';
        btn.textContent = item.label || item.state;
        btn.dataset.state = item.state;
        btn.dataset.file = item.file || '';

        // Select initial state or match currentState: an exact label wins over a shared state name
        // (D4 has two states named "success", the extraction and the inspection).
        const wanted = currentState && (availableStates.find(i => i.label === currentState) || availableStates.find(i => i.state === currentState));
        const isMatch = (wanted && item === wanted) || (!currentState && index === 0);

        if (isMatch) {
          btn.classList.add('active');
          currentState = item.label;
        }

        btn.addEventListener('click', async () => {
          // Remove active class from sibling buttons
          buttonsContainer.querySelectorAll('.btn-state').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          currentState = item.label;

          await activateState(item);
        });

        buttonsContainer.appendChild(btn);
      });

      // Automatically load the active state if none triggered yet
      const activeItem = availableStates.find(item => item.label === currentState) || availableStates.find(item => item.state === currentState) || availableStates[0];
      if (activeItem) {
        await activateState(activeItem);
      }

    } catch (err) {
      console.error('Failed to load states for screen:', currentScreen, err);
      buttonsContainer.innerHTML = '<span class="text-xs" style="color: var(--color-danger-text);">Error loading states</span>';
    }
  }

  /**
   * Load mock data and notify the application.
   */
  async function activateState(stateItem) {
    const metaBox = panelContainer.querySelector('#devMetaBox');
    try {
      const payload = await window.LabelLensData.loadScreen(currentScreen, stateItem.label, {
        file: stateItem.file,
        label: stateItem.label
      });

      if (metaBox) {
        metaBox.innerHTML = `
          <div><strong>Operation:</strong> ${escapeHtml(payload.operationId || 'none')}</div>
          <div><strong>HTTP Status:</strong> ${escapeHtml(String(payload.status || '200'))}</div>
          <div><strong>Schema:</strong> ${escapeHtml(payload.schema || 'none')}</div>
          <div><strong>File:</strong> ${escapeHtml(payload.file || 'Idle (no mock file)')}</div>
        `;
      }

      // Dispatch event to application views
      window.dispatchEvent(new CustomEvent('labellens:state-changed', {
        detail: {
          screen: currentScreen,
          state: stateItem.label || stateItem.state,
          meta: payload,
          data: payload.data
        }
      }));

    } catch (err) {
      if (metaBox) {
        metaBox.innerHTML = `<span style="color: #fca5a5;">Error: ${escapeHtml(err.message)}</span>`;
      }
    }
  }

  /**
   * Update the current screen and reload its valid states.
   * @param {string} newScreen
   * @param {string} [initialState]
   */
  async function setScreen(newScreen, initialState = null) {
    if (currentScreen === newScreen && currentState === initialState && initialState !== null) {
      return;
    }
    currentScreen = newScreen;
    if (initialState) {
      currentState = initialState;
    } else {
      currentState = null; // Let first available state be chosen
    }

    const select = panelContainer.querySelector('#devScreenSelect');
    if (select && select.value !== newScreen) {
      select.value = newScreen;
    }

    await refreshStates();

    // Notify app if user switched screen from dev panel
    window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
      detail: { screen: newScreen, state: currentState }
    }));
  }

  function escapeHtml(str) {
    if (window.LabelLensData && window.LabelLensData.escapeHtml) {
      return window.LabelLensData.escapeHtml(str);
    }
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Initialize once DOM is ready
  function init() {
    document.body.appendChild(panelContainer);
    renderPanel();
    refreshStates();

    // Listen for screen changes triggered by the main app navigation
    window.addEventListener('labellens:screen-changed', (event) => {
      if (event.detail && event.detail.screen && event.detail.screen !== currentScreen) {
        setScreen(event.detail.screen, event.detail.state || null);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose global controller
  window.LabelLensStateSwitcher = {
    setScreen,
    refreshStates,
    getCurrentScreen: () => currentScreen,
    getCurrentState: () => currentState
  };
})();
