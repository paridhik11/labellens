/**
 * ui/js/render-p1.js
 * Renderer for Screen P1: Scan and Understand (Mockup Panel 1)
 * 
 * Hard rules:
 * - Public medicine mode only (21 CFR 201, 208, 211).
 * - Never invent data. All values come from mock.
 * - Loading states show a clear loading screen, then the finished state.
 * - Any test identifier shows a visible TEST badge.
 * - No em dashes.
 */

(function() {
  let loadingTimer = null;

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

  function renderTestBadge(val) {
    if (window.LabelLensData && window.LabelLensData.renderTestBadge) {
      return window.LabelLensData.renderTestBadge(val);
    }
    return '';
  }

  function renderScreenP1(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    // Clear any pending transition timer from a previous state
    if (loadingTimer) {
      clearTimeout(loadingTimer);
      loadingTimer = null;
    }

    // 1. Loading State (public/scan/loading.json)
    if (state && state.includes('loading')) {
      const progressPercent = typeof safeData.progress === 'number'
        ? Math.round(safeData.progress * 100)
        : 50;
      const testBadge = renderTestBadge(safeData);

      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px 24px; max-width: 640px; margin: 0 auto;">
          <div style="font-size: 2.2rem; margin-bottom: 12px; animation: pulse 1.5s infinite;">🔍</div>
          <div class="text-xs font-semibold text-muted" style="margin-bottom: 6px;">
            Job ID: <code>${escapeHtml(safeData.job_id || '')}</code> ${testBadge}
          </div>
          <h3>${escapeHtml(safeData.message || 'Scanning medication package...')}</h3>
          <p class="text-muted text-sm" style="margin-top: 6px;">
            Kind: <strong>${escapeHtml(safeData.kind || 'public_scan')}</strong> | State: <strong>${escapeHtml(safeData.state || 'processing')}</strong>
          </p>

          <div style="width: 280px; height: 8px; background: #e2e8f0; border-radius: 99px; margin: 24px auto 12px auto; overflow: hidden; position: relative;">
            <div style="width: ${progressPercent}%; height: 100%; background: var(--color-primary-teal); border-radius: 99px; transition: width 0.3s ease;"></div>
          </div>
          <div class="text-xs text-muted" style="font-weight: 600;">Progress: ${progressPercent}%</div>

          <div style="margin-top: 28px; border-top: 1px solid var(--color-border); padding-top: 16px;">
            <button class="btn btn-sm btn-primary" type="button" id="btnP1SkipToFinished">
              Skip to finished state &rarr;
            </button>
          </div>
        </div>
      `;

      const proceedToFinished = () => {
        if (loadingTimer) {
          clearTimeout(loadingTimer);
          loadingTimer = null;
        }
        if (window.LabelLensStateSwitcher) {
          window.LabelLensStateSwitcher.setScreen('P2 Product information', 'success');
        } else {
          window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
            detail: { screen: 'P2 Product information' }
          }));
        }
      };

      const skipBtn = container.querySelector('#btnP1SkipToFinished');
      if (skipBtn) {
        skipBtn.addEventListener('click', proceedToFinished);
      }

      // Automatically transition to the finished state after clear display
      loadingTimer = setTimeout(proceedToFinished, 1800);
      return;
    }

    // 2. Failed State (public/scan/failed.json)
    if (state && state.includes('failed')) {
      const err = safeData.error || {};
      const testBadge = renderTestBadge(safeData);

      container.innerHTML = `
        <div style="max-width: 680px; margin: 0 auto;">
          <div class="notice-banner notice-danger">
            <div class="notice-icon">!</div>
            <div style="flex: 1;">
              <div class="flex-between">
                <div class="notice-title">Scan failed</div>
                ${testBadge}
              </div>
              <div class="notice-text" style="margin-top: 4px;">
                ${escapeHtml(err.message || 'The image could not be processed.')}
              </div>
              <div class="text-xs font-mono" style="margin-top: 8px; color: var(--color-danger-text);">
                Error Code: ${escapeHtml(err.error || 'unknown_error')} | Job ID: ${escapeHtml(safeData.job_id || '')} | State: ${escapeHtml(safeData.state || 'failed')}
              </div>
            </div>
          </div>

          <div class="card" style="text-align: center; padding: 24px;">
            <p class="text-sm text-muted">Please hold packaging flat in good lighting and avoid reflections or blur.</p>
            <div style="margin-top: 16px;">
              <button class="btn btn-primary" type="button" id="btnP1TryAgain">Try scanning again</button>
            </div>
          </div>
        </div>
      `;

      const tryAgainBtn = container.querySelector('#btnP1TryAgain');
      if (tryAgainBtn) {
        tryAgainBtn.addEventListener('click', () => {
          if (window.LabelLensStateSwitcher) {
            window.LabelLensStateSwitcher.setScreen('P1 Scan and Understand', 'empty (idle)');
          } else {
            window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
              detail: { screen: 'P1 Scan and Understand' }
            }));
          }
        });
      }
      return;
    }

    // 3. Empty / Idle State (Per SCREENS.md: idle screen, no request yet)
    container.innerHTML = `
      <div style="text-align: center; max-width: 600px; margin: 0 auto 24px auto;">
        <h2>Understand your label</h2>
        <p class="text-muted text-sm" style="margin-top: 8px;">Scan or upload a photo to extract and explain key information from a medical product label.</p>
        <div class="flex-row" style="justify-content: center; gap: 12px; margin-top: 16px;">
          <button class="btn btn-primary" type="button" id="btnP1UseCamera">Use camera</button>
          <button class="btn btn-secondary" type="button" id="btnP1UploadImage">Upload image</button>
        </div>
      </div>

      <div class="viewfinder-card" style="max-width: 680px; margin: 0 auto;">
        <div class="viewfinder-reticle reticle-tl"></div>
        <div class="viewfinder-reticle reticle-tr"></div>
        <div class="viewfinder-reticle reticle-bl"></div>
        <div class="viewfinder-reticle reticle-br"></div>
        <div style="color: #94a3b8; text-align: center;">
          <div style="font-size: 2rem; margin-bottom: 8px;">📷</div>
          <div class="font-semibold text-sm">Align medication packaging within the frame</div>
          <div class="text-xs text-muted" style="margin-top: 4px;">Capture all sides if needed (front, back, and both sides).</div>
        </div>
      </div>
    `;

    const startMockScan = () => {
      if (window.LabelLensStateSwitcher) {
        window.LabelLensStateSwitcher.setScreen('P1 Scan and Understand', 'loading');
      }
    };

    // api mode: a real file picker or camera capture, sent to publicScan, 202 job polled.
    const isApi = window.LabelLensData.CONFIG.mode === 'api';
    const note = document.createElement('div');
    note.className = 'text-xs text-muted';
    note.setAttribute('data-testid', 'p1-note');
    note.style.cssText = 'text-align:center;margin-top:10px;';
    container.appendChild(note);
    const picker = (capture) => {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      if (capture) input.setAttribute('capture', 'environment');
      input.setAttribute('data-testid', capture ? 'p1-camera-input' : 'p1-file-input');
      input.style.display = 'none';
      container.appendChild(input);
      input.addEventListener('change', async () => {
        const file = input.files[0];
        if (!file) return;
        note.textContent = 'Uploading...';
        try {
          const res = await window.LabelLensActions.publicScan(file, (j) => { note.textContent = `Scanning: ${j.state}${j.message ? ' (' + j.message + ')' : ''}`; });
          if (res.mock) {
            note.textContent = 'The public scan is answered with a mock by this server (X-Mock). Showing the mock product page.';
            window.LabelLensStateSwitcher.setScreen('P2 Product information', 'success');
          } else if (res.job.state === 'failed') {
            window.LabelLensStateSwitcher.setScreen('P1 Scan and Understand', 'failed');
          } else {
            window.LabelLensStateSwitcher.setScreen('P2 Product information', 'success');
          }
        } catch (e) {
          note.textContent = 'Scan failed: ' + e.message;
        }
      });
      input.click();
    };
    const cameraBtn = container.querySelector('#btnP1UseCamera');
    const uploadBtn = container.querySelector('#btnP1UploadImage');
    if (cameraBtn) cameraBtn.addEventListener('click', () => (isApi ? picker(true) : startMockScan()));
    if (uploadBtn) uploadBtn.addEventListener('click', () => (isApi ? picker(false) : startMockScan()));
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['P1 Scan and Understand'] = renderScreenP1;
  window.LabelLensRenderers['P1'] = renderScreenP1;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenP1 };
  }
})();
