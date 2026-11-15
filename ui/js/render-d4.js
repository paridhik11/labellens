/**
 * ui/js/render-d4.js
 * Renderer for Screen D4: Inspect ("Label review", Mockup Panel 3)
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Test identifiers labelled TEST.
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

  function renderScreenD4(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    // Loading state
    if (state === 'loading' || (safeData.state && safeData.state === 'processing')) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px; max-width: 600px; margin: 0 auto;">
          <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Job ID: <code>${escapeHtml(safeData.job_id || 'job_inspect_0001')}</code></div>
          <h3>Running regulatory inspection checks...</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">Evaluating text and barcode conformance against 21 CFR 801.</p>
          <div style="width: 280px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 24px auto; overflow: hidden;">
            <div style="width: 70%; height: 100%; background: var(--color-primary-blue);"></div>
          </div>
        </div>
      `;
      return;
    }

    // Extraction Needs Review State (unclear fields)
    if (state && state.includes('needs_review') && safeData.unclear_fields) {
      const unclear = safeData.unclear_fields || [];
      const fields = safeData.fields || {};
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Confirm extraction : Demo device</h2>
            <div class="text-xs text-muted">Version: <span class="badge badge-purple">${escapeHtml(safeData.version_id || 'lbv_0001')}</span></div>
          </div>
          <span class="badge badge-warning">Needs Review</span>
        </div>

        <div class="notice-banner notice-warning">
          <div class="notice-icon">i</div>
          <div>
            <div class="notice-title">Confirm extracted fields</div>
            <div class="notice-text">OCR extraction confidence was below threshold for ${unclear.length} field(s). Please confirm values before proceeding.</div>
          </div>
        </div>

        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Extracted Fields</div>
          <div class="kv-table">
            ${Object.entries(fields).map(([k, v]) => `
              <div class="kv-row">
                <span class="kv-label">${escapeHtml(k)}</span>
                <span class="kv-value">
                  ${unclear.includes(k) ? `
                    <span class="badge badge-warning">${escapeHtml(String(v))}</span>
                    <span class="text-xs text-muted" style="margin-left: 8px;">(unclear, needs verification)</span>
                  ` : escapeHtml(String(v))}
                </span>
              </div>
            `).join('')}
          </div>
          <div style="margin-top: 20px;">
            <button class="btn btn-primary" type="button">Confirm extraction</button>
          </div>
        </div>
      `;
      return;
    }

    // Standard Inspection Result View (Mockup Panel 3)
    const findings = safeData.findings || [];
    const criticalFinding = findings.find(f => f.severity === 'critical') || findings[0];
    const isPassed = safeData.passed === true;

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Label review : Demo device</h2>
          <div class="flex-row" style="margin-top: 4px; gap: 8px;">
            <span class="text-xs text-muted">Version:</span>
            <span class="badge badge-blue">Product P1</span>
            <span class="badge badge-purple">Artwork L2</span>
          </div>
        </div>
        <div class="flex-row">
          <span class="badge ${isPassed ? 'badge-teal' : 'badge-danger'}">
            ${isPassed ? 'Passed Inspection' : 'Needs Review'}
          </span>
        </div>
      </div>

      <div class="grid-two-col">
        <!-- Left: Simulated Device Label with Bounding Box -->
        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Device Label Artwork</span>
            <span class="badge badge-test">(01)00000000000000 [TEST]</span>
          </div>

          <div class="label-canvas-box" style="background: #ffffff; border: 2px solid #334155;">
            <div>
              <div style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">ExampleDevice™</div>
              <div class="text-xs text-muted" style="margin-top: 2px;">Sterile Medical Device | Single use only</div>
              <div class="flex-row" style="margin-top: 8px; gap: 12px;">
                <span style="border: 1px solid #0f172a; padding: 2px 6px; font-size: 0.75rem; font-weight: 700;">STERILE EO</span>
                <span style="border: 1px solid #0f172a; padding: 2px 6px; font-size: 0.75rem; font-weight: 700;">REF ED-100</span>
              </div>
            </div>

            <div style="margin: 20px 0;">
              <!-- Bounding Box Orange Reticle around Expiry -->
              <div class="label-bbox-highlight" style="display: inline-block;">
                <span class="text-xs font-semibold" style="color: #ea580c; display: block;">EXP 2028-04-30</span>
              </div>
            </div>

            <div>
              <div class="label-bbox-highlight" style="display: inline-block; padding: 6px;">
                <div class="font-mono text-xs font-semibold" style="letter-spacing: 2px;">|| | |||| | ||||| |||| |</div>
                <div class="font-mono text-xs" style="color: #64748b; margin-top: 2px;">(01)12345678901234 [TEST]</div>
              </div>
              <div class="text-xs text-muted" style="margin-top: 10px;">
                Example Devices Ltd | Sample City, Country
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Findings and Observed vs Reference -->
        <div class="flex-col" style="gap: 16px;">
          ${criticalFinding ? `
            <div class="notice-banner notice-danger" style="margin-bottom: 0;">
              <div class="notice-icon">!</div>
              <div style="flex: 1;">
                <div class="flex-between">
                  <span class="notice-title">${escapeHtml(criticalFinding.kind.replace('_', ' '))}</span>
                  <span class="badge badge-danger">Needs review</span>
                </div>
                <div class="notice-text" style="margin-top: 4px;">${escapeHtml(criticalFinding.message)}</div>
              </div>
            </div>

            <div class="card">
              <div class="card-header-clean font-semibold text-sm">Observed vs reference</div>
              <div class="kv-table">
                <div class="kv-row">
                  <span class="kv-label">Printed on label</span>
                  <span class="kv-value"><span class="badge badge-danger">${escapeHtml(criticalFinding.observed || '2028-04-30')}</span></span>
                </div>
                <div class="kv-row">
                  <span class="kv-label">From barcode (reference)</span>
                  <span class="kv-value"><span class="badge badge-danger">${escapeHtml(criticalFinding.expected || '2028-03-31')}</span></span>
                </div>
              </div>

              ${criticalFinding.citations && criticalFinding.citations.length > 0 ? `
                <div style="margin-top: 14px; background: var(--color-bg-subtle); padding: 10px; border-radius: var(--radius-md);">
                  <div class="text-xs font-semibold text-muted">Retrieved Regulatory Requirement:</div>
                  <div class="text-xs" style="margin-top: 2px;">21 CFR ${escapeHtml(criticalFinding.citations[0].section || '')} : ${escapeHtml(criticalFinding.citations[0].title || '')}</div>
                </div>
              ` : ''}
            </div>
          ` : `
            <div class="card" style="text-align: center; padding: 32px;">
              <div style="color: var(--color-success-text); font-size: 2rem;">✓</div>
              <div class="font-semibold" style="margin-top: 8px;">All label checks passed</div>
              <div class="text-xs text-muted" style="margin-top: 4px;">Extraction confirmed against 21 CFR 801 requirements.</div>
            </div>
          `}

          <div class="flex-between" style="margin-top: 8px;">
            <button class="btn btn-primary" type="button">Confirm extraction</button>
            <button class="btn btn-secondary" type="button" id="btnExportInspectReport">Export report</button>
          </div>
        </div>
      </div>
    `;

    const exportBtn = container.querySelector('#btnExportInspectReport');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
          detail: { screen: 'D8 Export' }
        }));
      });
    }
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D4 Inspect'] = renderScreenD4;
  window.LabelLensRenderers['D4'] = renderScreenD4;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD4 };
  }
})();
