/**
 * ui/js/render-d3.js
 * Renderer for Screen D3: Upload or scan
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
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

  function renderScreenD3(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    if (state === 'loading' || (safeData.state && safeData.state === 'processing')) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px; max-width: 600px; margin: 0 auto;">
          <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Job ID: <code>${escapeHtml(safeData.job_id || 'job_upload_0001')}</code></div>
          <h3>Uploading and pre-processing device label...</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">Kind: ${escapeHtml(safeData.kind || 'upload_scan')} | Status: <strong>${escapeHtml(safeData.state || 'processing')}</strong></p>
          <div style="width: 280px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 24px auto; overflow: hidden;">
            <div style="width: 55%; height: 100%; background: var(--color-primary-blue);"></div>
          </div>
          <div class="text-xs text-muted">Calculating SHA256 checksum and running OCR detection pipeline.</div>
        </div>
      `;
      return;
    }

    if (state === 'failed' || (safeData.state && safeData.state === 'failed')) {
      const err = safeData.error || {};
      container.innerHTML = `
        <div class="notice-banner notice-danger" style="max-width: 680px; margin: 0 auto 20px auto;">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">Upload processing failed</div>
            <div class="notice-text">${escapeHtml(err.message || 'File parsing or image decoding failed.')}</div>
          </div>
        </div>
        <div class="card" style="text-align: center; padding: 36px; max-width: 680px; margin: 0 auto;">
          <p class="text-muted text-sm">Please verify the label file is a valid PNG, JPEG or single-page PDF under 20MB.</p>
          <button class="btn btn-secondary" type="button" style="margin-top: 16px;">Try upload again</button>
        </div>
      `;
      return;
    }

    // Success State
    const file = safeData.file || {};
    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Scan processed: <code>${escapeHtml(safeData.scan_id || 'scn_0001')}</code></h2>
          <div class="text-xs text-muted">Product: <code>${escapeHtml(safeData.product_id || '')}</code> | Version: <code>${escapeHtml(safeData.version_id || '')}</code></div>
        </div>
        <span class="badge badge-teal">Scan Ready</span>
      </div>

      <div class="grid-two-col">
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">File Metadata</div>
          <div class="kv-table">
            <div class="kv-row">
              <span class="kv-label">File ID</span>
              <span class="kv-value"><code>${escapeHtml(file.file_id || 'fil_0001')}</code></span>
            </div>
            <div class="kv-row">
              <span class="kv-label">MIME Type</span>
              <span class="kv-value">${escapeHtml(file.mime || 'image/png')}</span>
            </div>
            <div class="kv-row">
              <span class="kv-label">Pages</span>
              <span class="kv-value">${file.pages || 1}</span>
            </div>
            <div class="kv-row">
              <span class="kv-label">SHA256</span>
              <span class="kv-value font-mono text-xs" style="word-break: break-all;">${escapeHtml(file.sha256 || '')}</span>
            </div>
            <div class="kv-row">
              <span class="kv-label">Created</span>
              <span class="kv-value">${escapeHtml(safeData.created_at || '')}</span>
            </div>
          </div>
        </div>

        <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div class="card-header-clean font-semibold text-sm">Next Step: Inspect &amp; Extract</div>
            <p class="text-muted text-sm">
              The label image has been registered. You can now run OCR extraction, inspect bounding boxes against 21 CFR 801, and verify UDI barcode data.
            </p>
          </div>
          <div style="margin-top: 24px;">
            <button class="btn btn-primary" type="button" style="width: 100%;" id="btnGoToInspect">Inspect this label now &rarr;</button>
          </div>
        </div>
      </div>
    `;

    const inspectBtn = container.querySelector('#btnGoToInspect');
    if (inspectBtn) {
      inspectBtn.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
          detail: { screen: 'D4 Inspect' }
        }));
      });
    }
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D3 Upload or scan'] = renderScreenD3;
  window.LabelLensRenderers['D3'] = renderScreenD3;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD3 };
  }
})();
