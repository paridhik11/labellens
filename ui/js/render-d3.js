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

  function renderStateD3(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    if (state === 'loading' || (safeData.state && safeData.state === 'processing')) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px; max-width: 600px; margin: 0 auto;">
          <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Job ID: <code>${escapeHtml(safeData.job_id || 'job_upload_0001')}</code></div>
          <h3>Uploading and pre-processing device label...</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">Kind: ${escapeHtml(safeData.kind || 'upload_scan')} | Status: <strong>${escapeHtml(safeData.state || 'processing')}</strong></p>
          <div style="width: 280px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 24px auto; overflow: hidden;">
            <div style="width: ${Math.round((typeof safeData.progress === 'number' ? safeData.progress : 0.55) * 100)}%; height: 100%; background: var(--color-primary-blue);"></div>
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
            <div class="notice-title">${err.error === 'retake_photo' ? 'Retake the photo' : 'Upload processing failed'}</div>
            <div class="notice-text">${escapeHtml(err.message || 'File parsing or image decoding failed.')}</div>
            ${err.error === 'retake_photo' && err.details && Array.isArray(err.details.reasons) ? `<div class="notice-text" data-testid="retake-reasons" style="margin-top: 6px;">Reasons: <strong>${err.details.reasons.map(escapeHtml).join(', ')}</strong>. No label version was created.</div>` : ''}
          </div>
        </div>
        <div class="card" style="text-align: center; padding: 36px; max-width: 680px; margin: 0 auto;">
          <p class="text-muted text-sm">Please check that the label file is a valid PNG, JPEG or PDF under 15 MB.</p>
          <button class="btn btn-secondary" type="button" style="margin-top: 16px;" id="btnTryUploadAgain">Try upload again</button>
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

  /** Upload card on top of every D3 state. Real upload only in api mode (product_id is required, CR-20). */
  function renderScreenD3(container, state, meta, data) {
    if (!container) return;
    const isApi = window.LabelLensData.CONFIG.mode === 'api';
    const known = (window.LabelLensData.CONFIG.ids || {}).product_id || (data && data.product_id) || '';
    container.innerHTML = `
      <div class="card" style="margin-bottom: 16px;" data-testid="upload-card">
        <div class="card-header-clean font-semibold text-sm">Upload a label (PNG, JPEG or PDF, up to 15 MB)</div>
        <div class="flex-row" style="gap: 10px; flex-wrap: wrap; align-items: flex-end;">
          <div><label class="text-xs text-muted" for="d3File">File</label><br><input type="file" id="d3File" accept="image/png,image/jpeg,application/pdf"></div>
          <div><label class="text-xs text-muted" for="d3Product">Product id (required)</label><br><input type="text" id="d3Product" value="${escapeHtml(known)}" placeholder="product id" style="padding: 6px 8px; border: 1px solid var(--color-border); border-radius: var(--radius-md);"></div>
          <div><label class="text-xs text-muted" for="d3Source">Source</label><br><select id="d3Source"><option value="upload">upload</option><option value="camera">camera</option></select></div>
          <button class="btn btn-primary" type="button" id="d3Upload">Upload</button>
          <button class="btn btn-secondary" type="button" id="d3Photo">Take photo</button>
          <input type="file" id="d3PhotoInput" accept="image/*" capture="environment" style="display:none" data-testid="d3-photo-input">
        </div>
        <div class="text-xs text-muted" id="d3Note" style="margin-top: 8px;">${isApi ? 'Runs the photo-quality gate, then the extractor. A blurry photo is answered with retake_photo and creates no version.' : 'Mock mode: nothing is uploaded. Open the page with ?mode=api to upload for real.'}</div>
      </div>
      <div id="d3State"></div>`;
    const stateBox = container.querySelector('#d3State');
    renderStateD3(stateBox, state, meta, data);
    const note = container.querySelector('#d3Note');
    const tryAgain = stateBox.querySelector('#btnTryUploadAgain');
    if (tryAgain) tryAgain.addEventListener('click', () => { container.querySelector('#d3File').click(); });
    const run = async (file, source) => {
      const pid = container.querySelector('#d3Product').value.trim();
      if (!isApi) { note.textContent = 'Mock mode: nothing was uploaded.'; return; }
      if (!file) { note.textContent = 'Choose a file first.'; return; }
      if (!pid) { note.textContent = 'A product id is required.'; return; }
      note.textContent = 'Uploading...';
      try {
        const res = await window.LabelLensActions.uploadScan(file, pid, source, (j) => {
          renderStateD3(stateBox, 'loading', null, j);
        });
        if (res.job.state === 'failed') {
          renderStateD3(stateBox, 'failed', null, res.job);
          note.textContent = '';
        } else if (!res.scan) {
          note.textContent = 'The job finished but the scan record could not be read. Nothing is shown rather than a guess.';
        } else {
          window.LabelLensData.setIds({ product_id: pid, label_id: res.scan.label_id, version_id: res.scan.version_id });
          renderStateD3(stateBox, 'success', null, res.scan);
          note.textContent = '';
        }
      } catch (e) {
        note.textContent = 'Upload failed: ' + e.message;
      }
    };
    container.querySelector('#d3Upload').addEventListener('click', () => {
      run(container.querySelector('#d3File').files[0], container.querySelector('#d3Source').value);
    });
    const photoInput = container.querySelector('#d3PhotoInput');
    container.querySelector('#d3Photo').addEventListener('click', () => {
      if (!isApi) { note.textContent = 'Mock mode: nothing was uploaded.'; return; }
      photoInput.click();
    });
    photoInput.addEventListener('change', () => run(photoInput.files[0], 'camera'));
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D3 Upload or scan'] = renderScreenD3;
  window.LabelLensRenderers['D3'] = renderScreenD3;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD3 };
  }
})();
