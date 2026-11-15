/**
 * ui/js/render-d10.js
 * Renderer for Screen D10: Print verification
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Closed-loop physical print verification.
 * - Report per condition (clean, scan, photo).
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

  function renderScreenD10(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    // Loading State
    if (state === 'loading' || (safeData.state && safeData.state === 'processing')) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px; max-width: 600px; margin: 0 auto;">
          <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Job ID: <code>${escapeHtml(safeData.job_id || 'job_pvf_0001')}</code></div>
          <h3>Verifying physical printed label scan...</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">Comparing OCR reading and DataMatrix decode against approved golden master.</p>
          <div style="width: 280px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 24px auto; overflow: hidden;">
            <div style="width: 75%; height: 100%; background: var(--color-primary-blue);"></div>
          </div>
        </div>
      `;
      return;
    }

    // Empty State
    if (state === 'empty' || (Array.isArray(safeData) && safeData.length === 0) || (safeData.items && safeData.items.length === 0)) {
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Print verification</h2>
            <div class="text-xs text-muted">Closed-loop physical print verification against approved master.</div>
          </div>
        </div>
        <div class="card" style="text-align: center; padding: 48px;">
          <h3>No print verifications on record</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">Upload a high-resolution photo or scan of a printed label roll or blister pack to verify.</p>
        </div>
      `;
      return;
    }

    // Verification Result View
    const outcome = safeData.outcome || (state === 'success' ? 'match' : (state === 'needs_review' ? 'rescan_needed' : 'mismatch'));
    const isMatch = outcome === 'match';
    const isRescan = outcome === 'rescan_needed';
    const mismatches = safeData.mismatches || [];
    const quality = safeData.quality || {};
    const barcode = safeData.barcode || {};

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Print Verification: <code>${escapeHtml(safeData.verification_id || 'pvf_0001')}</code></h2>
          <div class="text-xs text-muted">Version: <code>${escapeHtml(safeData.version_id || 'lbv_0003')}</code> | Condition: <span class="badge badge-blue">${escapeHtml(safeData.condition || 'photo')}</span></div>
        </div>
        <span class="badge ${isMatch ? 'badge-teal' : (isRescan ? 'badge-warning' : 'badge-danger')}">
          ${isMatch ? 'MATCH' : (isRescan ? 'RESCAN NEEDED' : 'MISMATCH')}
        </span>
      </div>

      ${isRescan ? `
        <div class="notice-banner notice-warning">
          <div class="notice-icon">i</div>
          <div>
            <div class="notice-title">Rescan Required : Image Quality Warning</div>
            <div class="notice-text">High glare or blur detected. Please capture with diffuse lighting and avoid direct flash.</div>
          </div>
        </div>
      ` : ''}

      ${!isMatch && !isRescan ? `
        <div class="notice-banner notice-danger">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">Print Discrepancy Detected</div>
            <div class="notice-text">${mismatches.length} printed element(s) do not match the approved artwork master.</div>
          </div>
        </div>
      ` : ''}

      <div class="grid-two-col">
        <!-- Findings / Mismatches -->
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Print Inspection Results</div>
          
          ${mismatches.length > 0 ? `
            <div class="flex-col" style="gap: 10px;">
              ${mismatches.map(m => `
                <div class="card" style="border: 1px solid var(--color-border); padding: 12px;">
                  <div class="font-semibold text-xs" style="color: var(--color-danger-text);">${escapeHtml(m.field || 'field')} discrepancy</div>
                  <div class="kv-table" style="margin-top: 6px;">
                    <div class="kv-row">
                      <span class="kv-label">Observed (Print)</span>
                      <span class="kv-value"><span class="badge badge-danger">${escapeHtml(m.observed)}</span></span>
                    </div>
                    <div class="kv-row">
                      <span class="kv-label">Expected (Master)</span>
                      <span class="kv-value"><span class="badge badge-teal">${escapeHtml(m.expected)}</span></span>
                    </div>
                  </div>
                </div>
              `).join('')}
            </div>
          ` : `
            <div style="text-align: center; padding: 24px;">
              <div style="color: var(--color-success-text); font-size: 2rem;">✓</div>
              <div class="font-semibold" style="margin-top: 8px;">All printed text matches approved master</div>
            </div>
          `}
        </div>

        <!-- Barcode and Quality -->
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">2D Barcode Verification</div>
          
          <div class="kv-table">
            <div class="kv-row">
              <span class="kv-label">Barcode Match</span>
              <span class="kv-value"><span class="badge ${barcode.match ? 'badge-teal' : 'badge-danger'}">${barcode.match ? 'Passed' : 'Failed'}</span></span>
            </div>
            ${barcode.decoded ? `
              <div class="kv-row">
                <span class="kv-label">Symbology</span>
                <span class="kv-value">${escapeHtml(barcode.decoded.type || 'DataMatrix')}</span>
              </div>
              <div class="kv-row">
                <span class="kv-label">Raw Data</span>
                <span class="kv-value font-mono text-xs" style="word-break: break-all;">${escapeHtml(barcode.decoded.raw || '')}</span>
              </div>
            ` : ''}
          </div>

          <div style="margin-top: 16px; border-top: 1px solid var(--color-border); padding-top: 12px;">
            <div class="text-xs font-semibold text-muted" style="margin-bottom: 6px;">Image Quality Metrics</div>
            <div class="flex-row" style="gap: 16px;">
              <span class="text-xs">Blur: <strong>${quality.blur !== undefined ? quality.blur : 'N/A'}</strong></span>
              <span class="text-xs">Glare: <strong>${quality.glare !== undefined ? quality.glare : 'N/A'}</strong></span>
              <span class="text-xs">Confidence: <strong>${quality.confidence !== undefined ? Math.round(quality.confidence * 100) + '%' : 'N/A'}</strong></span>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D10 Print verification'] = renderScreenD10;
  window.LabelLensRenderers['D10'] = renderScreenD10;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD10 };
  }
})();
