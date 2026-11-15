/**
 * ui/js/render-p1.js
 * Renderer for Screen P1: Scan and Understand (Mockup Panel 1)
 * 
 * Hard rules:
 * - Public medicine mode only (21 CFR 201, 208, 211).
 * - Never invent data.
 * - No em dashes.
 */

(function() {
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

  function renderScreenP1(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    if (state && state.includes('loading')) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 40px;">
          <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Job ID: ${escapeHtml(safeData.job_id || 'job_0001')}</div>
          <h3>Scanning medication package...</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">Kind: ${escapeHtml(safeData.kind || 'public_scan')} | State: <strong>${escapeHtml(safeData.state || 'processing')}</strong></p>
          <div style="width: 240px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 20px auto; overflow: hidden;">
            <div style="width: 65%; height: 100%; background: var(--color-primary-teal);"></div>
          </div>
        </div>
      `;
      return;
    }

    if (state && state.includes('failed')) {
      const err = safeData.error || {};
      container.innerHTML = `
        <div class="notice-banner notice-danger">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">Scan failed</div>
            <div class="notice-text">${escapeHtml(err.message || 'The image could not be processed. Please capture clear lighting with no glare.')}</div>
          </div>
        </div>
      `;
      return;
    }

    // Idle empty state (Ready to scan or upload)
    container.innerHTML = `
      <div style="text-align: center; max-width: 600px; margin: 0 auto 24px auto;">
        <h2>Understand your label</h2>
        <p class="text-muted text-sm" style="margin-top: 8px;">Scan or upload a photo to extract and explain key information from a medical product label.</p>
        <div class="flex-row" style="justify-content: center; gap: 12px; margin-top: 16px;">
          <button class="btn btn-primary" type="button">Use camera</button>
          <button class="btn btn-secondary" type="button">Upload image</button>
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
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['P1 Scan and Understand'] = renderScreenP1;
  window.LabelLensRenderers['P1'] = renderScreenP1;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenP1 };
  }
})();
