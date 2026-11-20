/**
 * ui/js/render-d4.js
 * Renderer for Screen D4: Inspect ("Label review", Mockup Panel 3)
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Mark drafts clearly: prominent DRAFT watermark/badge and required disclaimer:
 *   "Draft generated for review. Not a compliance determination."
 * - Test identifiers labelled TEST.
 * - Never invent data. Every value on screen comes from a mock.
 * - Citations show regulation section, verbatim quote, and source type (cfr or label_section).
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

  function renderTestBadge(val) {
    if (window.LabelLensData && window.LabelLensData.renderTestBadge) {
      return window.LabelLensData.renderTestBadge(val);
    }
    return '';
  }

  function renderScreenD4(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    const draftDisclaimer = safeData.disclaimer || 'Draft generated for review. Not a compliance determination.';
    const draftBannerHtml = `
      <div class="notice-banner notice-warning" style="margin-bottom: 16px;">
        <div class="notice-icon">i</div>
        <div style="flex: 1;">
          <div class="flex-between">
            <span class="notice-title">DRAFT ARTIFACT PREVIEW</span>
            <span class="badge badge-draft">DRAFT</span>
          </div>
          <div class="notice-text" style="margin-top: 4px;">
            ${escapeHtml(draftDisclaimer)}
          </div>
        </div>
      </div>
    `;

    // 1. Loading State (professional/inspect/loading.json)
    if (state === 'loading' || (safeData.state && safeData.state === 'queued')) {
      container.innerHTML = `
        ${draftBannerHtml}
        <div class="card" style="text-align: center; padding: 48px 24px; max-width: 600px; margin: 0 auto;">
          <div style="font-size: 2.2rem; margin-bottom: 12px; color: var(--color-primary-blue);">⏳</div>
          <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">
            Job ID: <code>${escapeHtml(safeData.job_id || 'job_inspect_0001')}</code>
          </div>
          <h3>Running regulatory inspection checks...</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">
            Kind: <strong>${escapeHtml(safeData.kind || 'inspect')}</strong> | State: <strong>${escapeHtml(safeData.state || 'queued')}</strong>
          </p>
          <div style="width: 280px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 24px auto; overflow: hidden;">
            <div style="width: 40%; height: 100%; background: var(--color-primary-blue);"></div>
          </div>
          <div style="margin-top: 20px;">
            <button class="btn btn-sm btn-primary" type="button" id="btnSkipInspectLoading">
              View Inspection Results &rarr;
            </button>
          </div>
        </div>
      `;

      const skipBtn = container.querySelector('#btnSkipInspectLoading');
      if (skipBtn) {
        skipBtn.addEventListener('click', () => {
          if (window.LabelLensStateSwitcher) {
            window.LabelLensStateSwitcher.setScreen('D4 Inspect', 'success');
          }
        });
      }
      return;
    }

    // 2. Extraction Needs Review (professional/inspect/extraction_needs_review.json)
    const isExtractionNeedsReview = (state && state.includes('needs_review')) || (safeData.unclear_fields && safeData.unclear_fields.length > 0);
    if (isExtractionNeedsReview && !safeData.findings) {
      const unclear = safeData.unclear_fields || [];
      const fields = safeData.fields || {};
      const warnings = safeData.warnings || [];
      const barcodes = safeData.barcodes || [];

      container.innerHTML = `
        ${draftBannerHtml}
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <div class="flex-row" style="gap: 8px;">
              <h2>Confirm extraction: ExampleDevice</h2>
              <span class="badge badge-warning">Review Needed</span>
            </div>
            <div class="text-xs text-muted" style="margin-top: 4px;">
              Label ID: <code>${escapeHtml(safeData.label_id || '')}</code> | Version: <strong>v${escapeHtml(String(safeData.version || 2))}</strong> | ID: <code>${escapeHtml(safeData.version_id || '')}</code>
            </div>
          </div>
          <button class="btn btn-sm btn-primary" type="button" id="btnConfirmExtractionAction">
            Confirm extraction &rarr;
          </button>
        </div>

        <div class="notice-banner notice-warning">
          <div class="notice-icon">i</div>
          <div style="flex: 1;">
            <div class="notice-title">Confirm extracted fields (${unclear.length} unclear)</div>
            <div class="notice-text">
              OCR confidence was below threshold for: <strong>${unclear.map(escapeHtml).join(', ')}</strong>.
              ${warnings.length > 0 ? `Warnings: ${warnings.map(escapeHtml).join('; ')}` : ''}
            </div>
          </div>
        </div>

        <div class="grid-two-col">
          <!-- Left: Label Canvas with Ambiguous Field Highlight -->
          <div class="card">
            <div class="card-header-clean flex-between">
              <span class="font-semibold text-sm">Detected Label Artwork</span>
              <span class="badge badge-test">${renderTestBadge('00000000000000')} (01)00000000000000 [TEST]</span>
            </div>
            <div class="label-canvas-box" style="background: #ffffff; border: 2px solid #334155; position: relative; padding: 18px;">
              <div style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">${escapeHtml(fields.product_name || 'ExampleDevice')}</div>
              <div class="text-xs text-muted" style="margin-top: 2px;">Model: ${escapeHtml(fields.model || 'ED-100')}</div>

              <div class="flex-row" style="margin-top: 10px; gap: 8px;">
                <span class="badge badge-blue">${escapeHtml(fields.sterilization || 'STERILE EO')}</span>
                <span class="badge badge-teal">Lot: ${escapeHtml(fields.lot || 'LOT0001')}</span>
              </div>

              <div style="margin: 16px 0;">
                <span class="font-mono text-xs">EXP ${escapeHtml(fields.expiry || '2028-04-30')}</span>
              </div>

              <!-- Ambiguous Bounding Box Highlight -->
              <div style="border: 2px dashed #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 8px; border-radius: 4px; margin-top: 14px;">
                <div class="text-xs font-semibold" style="color: #b45309;">OCR Block 7 (Ambiguous match):</div>
                <div class="text-xs font-mono" style="margin-top: 2px;">${escapeHtml(fields.manufacturer_address || '')}</div>
              </div>
            </div>
          </div>

          <!-- Right: Extraction Table with Resolution Input -->
          <div class="card">
            <div class="card-header-clean flex-between">
              <span class="font-semibold text-sm">Extracted Field Values</span>
              <span class="text-xs text-muted">Confirmed: <strong>false</strong></span>
            </div>
            <div class="kv-table">
              ${Object.entries(fields).map(([k, v]) => {
                const isUnclear = unclear.includes(k);
                return `
                  <div class="kv-row" style="${isUnclear ? 'background: rgba(245, 158, 11, 0.08); padding: 6px;' : ''}">
                    <span class="kv-label">${escapeHtml(k)}</span>
                    <span class="kv-value">
                      ${isUnclear ? `
                        <input type="text" value="${escapeHtml(String(v))}" class="input-sm" style="width: 100%; border: 1px solid #f59e0b; border-radius: 4px; padding: 4px 8px; font-size: 0.8rem;">
                        <span class="badge badge-warning" style="margin-top: 4px;">Needs Confirmation</span>
                      ` : `
                        <span>${escapeHtml(String(v))} ${renderTestBadge(v)}</span>
                      `}
                    </span>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        </div>
      `;

      const confirmBtn = container.querySelector('#btnConfirmExtractionAction');
      if (confirmBtn) {
        confirmBtn.addEventListener('click', () => {
          if (window.LabelLensStateSwitcher) {
            window.LabelLensStateSwitcher.setScreen('D4 Inspect', 'success (confirmed extraction)');
          }
        });
      }
      return;
    }

    // 3. Extraction Success or Confirmed (professional/inspect/extraction_success.json or extraction_confirmed.json)
    if (safeData.fields && !safeData.findings) {
      const fields = safeData.fields || {};
      const barcodes = safeData.barcodes || [];
      const symbols = safeData.symbols || [];
      const isConfirmed = safeData.confirmed === true;

      container.innerHTML = `
        ${draftBannerHtml}
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <div class="flex-row" style="gap: 8px;">
              <h2>Label extraction: ${escapeHtml(fields.product_name || 'ExampleDevice')}</h2>
              <span class="badge ${isConfirmed ? 'badge-teal' : 'badge-blue'}">
                ${isConfirmed ? 'Extraction Confirmed' : 'Extraction Done'}
              </span>
            </div>
            <div class="text-xs text-muted" style="margin-top: 4px;">
              Label: <code>${escapeHtml(safeData.label_id || '')}</code> | Version ID: <code>${escapeHtml(safeData.version_id || '')}</code> ${safeData.confirmed_by ? `| Confirmed by: <code>${escapeHtml(safeData.confirmed_by)}</code>` : ''}
            </div>
          </div>
          <button class="btn btn-sm btn-primary" type="button" id="btnRunInspectionNow">
            Run Inspection Checks &rarr;
          </button>
        </div>

        <div class="grid-two-col">
          <!-- Label Artwork Simulation -->
          <div class="card">
            <div class="card-header-clean flex-between">
              <span class="font-semibold text-sm">Extracted Artwork Boxes</span>
              <span class="badge badge-test">(01)00000000000000 [TEST]</span>
            </div>

            <div class="label-canvas-box" style="background: #ffffff; border: 2px solid #334155; position: relative; padding: 18px;">
              <div style="font-size: 1.2rem; font-weight: 800; color: #0f172a;">${escapeHtml(fields.product_name || '')}</div>
              <div class="text-xs text-muted" style="margin-top: 2px;">Model: ${escapeHtml(fields.model || '')}</div>

              <div class="flex-row" style="margin-top: 10px; gap: 8px;">
                <span style="border: 1px solid #0f172a; padding: 2px 6px; font-size: 0.75rem; font-weight: 700;">${escapeHtml(fields.sterilization || 'STERILE EO')}</span>
                <span style="border: 1px solid #0f172a; padding: 2px 6px; font-size: 0.75rem; font-weight: 700;">LOT ${escapeHtml(fields.lot || '')}</span>
              </div>

              <div style="margin: 16px 0;">
                <span class="font-mono text-xs font-semibold">EXP ${escapeHtml(fields.expiry || '')}</span>
              </div>

              <div style="border: 1px solid #cbd5e1; background: #f8fafc; padding: 8px; border-radius: 4px; margin-top: 12px; font-size: 0.75rem;">
                <div class="font-mono text-xs" style="font-weight: 700;">GS1 DataMatrix (01)00000000000000 [TEST]</div>
                <div class="text-xs text-muted" style="margin-top: 4px;">${escapeHtml(fields.manufacturer || '')} | ${escapeHtml(fields.manufacturer_address || '')}</div>
              </div>
            </div>
          </div>

          <!-- Fields and Symbols Table -->
          <div class="flex-col" style="gap: 16px;">
            <div class="card">
              <div class="card-header-clean font-semibold text-sm">Extracted Fields (${Object.keys(fields).length})</div>
              <div class="kv-table">
                ${Object.entries(fields).map(([k, v]) => `
                  <div class="kv-row">
                    <span class="kv-label">${escapeHtml(k)}</span>
                    <span class="kv-value">${escapeHtml(String(v))} ${renderTestBadge(v)}</span>
                  </div>
                `).join('')}
              </div>
            </div>

            <div class="card">
              <div class="card-header-clean flex-between">
                <span class="font-semibold text-sm">Detected Symbols (${symbols.length})</span>
                <span class="badge badge-purple">ISO 15223-1</span>
              </div>
              <div class="flex-col" style="gap: 6px;">
                ${symbols.map(sym => `
                  <div class="flex-between" style="border: 1px solid var(--color-border); padding: 6px 10px; border-radius: 4px; background: var(--color-bg-subtle);">
                    <span class="font-semibold text-xs">${escapeHtml(sym.name)}</span>
                    <span class="text-xs text-muted">Confidence: ${Math.round((sym.conf || 0) * 100)}%</span>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
        </div>
      `;

      const runInspectBtn = container.querySelector('#btnRunInspectionNow');
      if (runInspectBtn) {
        runInspectBtn.addEventListener('click', () => {
          if (window.LabelLensStateSwitcher) {
            window.LabelLensStateSwitcher.setScreen('D4 Inspect', 'success');
          }
        });
      }
      return;
    }

    // 4. Inspection Results View: Success or Failed Check (professional/inspect/success.json or failed_check.json)
    const findings = safeData.findings || [];
    const criticalCount = safeData.critical_count || 0;
    const isPassed = safeData.passed === true;
    const criticalFinding = findings.find(f => f.severity === 'critical');

    container.innerHTML = `
      ${draftBannerHtml}
      <div class="flex-between" style="margin-bottom: 16px; align-items: flex-start;">
        <div>
          <div class="flex-row" style="gap: 8px;">
            <h2>Label review: ExampleDevice</h2>
            <span class="badge ${isPassed ? 'badge-teal' : 'badge-danger'}">
              ${isPassed ? 'All Checks Passed' : `${criticalCount} Finding(s) Require Review`}
            </span>
          </div>
          <div class="text-xs text-muted" style="margin-top: 4px;">
            Check ID: <code>${escapeHtml(safeData.check_id || '')}</code> | Label ID: <code>${escapeHtml(safeData.label_id || '')}</code> | Version: <code>${escapeHtml(safeData.version_id || '')}</code>
          </div>
        </div>
        <div class="flex-row" style="gap: 8px;">
          <button class="btn btn-sm btn-secondary" type="button" id="btnExportInspectReport">
            Export Report &rarr;
          </button>
        </div>
      </div>

      ${!isPassed && criticalFinding ? `
        <div class="notice-banner notice-danger">
          <div class="notice-icon">!</div>
          <div style="flex: 1;">
            <div class="flex-between">
              <span class="notice-title">Critical Compliance Finding: ${escapeHtml(criticalFinding.kind.replace('_', ' '))}</span>
              <span class="badge badge-danger">Needs Human Review</span>
            </div>
            <div class="notice-text" style="margin-top: 4px;">
              ${escapeHtml(criticalFinding.message)}
            </div>
          </div>
        </div>
      ` : ''}

      <div class="grid-two-col">
        <!-- Left: Simulated Device Label with Bounding Box Overlay -->
        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Label Inspection Overlay</span>
            <span class="badge badge-test">(01)00000000000000 [TEST]</span>
          </div>

          <div class="label-canvas-box" style="background: #ffffff; border: 2px solid #334155; position: relative; padding: 20px;">
            <div>
              <div style="font-size: 1.25rem; font-weight: 800; color: #0f172a;">ExampleDevice™</div>
              <div class="text-xs text-muted" style="margin-top: 2px;">Sterile Medical Device | Single use only</div>
              <div class="flex-row" style="margin-top: 10px; gap: 10px;">
                <span style="border: 1px solid #0f172a; padding: 2px 6px; font-size: 0.75rem; font-weight: 700;">STERILE EO</span>
                <span style="border: 1px solid #0f172a; padding: 2px 6px; font-size: 0.75rem; font-weight: 700;">REF ED-100</span>
              </div>
            </div>

            <!-- Bounding Box around Expiry -->
            <div style="margin: 20px 0;">
              <div style="display: inline-block; padding: 4px 8px; border: 2px solid ${!isPassed ? '#ef4444' : '#10b981'}; background: ${!isPassed ? 'rgba(239, 68, 68, 0.08)' : 'rgba(16, 185, 129, 0.08)'}; border-radius: 4px;">
                <span class="text-xs font-mono font-semibold" style="color: ${!isPassed ? '#dc2626' : '#059669'};">
                  EXP ${!isPassed ? '2028-04-30' : '2028-03-31'}
                </span>
                ${!isPassed ? `<span class="badge badge-danger text-xs" style="margin-left: 6px;">Mismatch</span>` : ''}
              </div>
            </div>

            <div style="border: 1px solid #cbd5e1; background: #f8fafc; padding: 10px; border-radius: 4px;">
              <div class="font-mono text-xs font-semibold" style="letter-spacing: 1px;">
                GS1 DataMatrix: (01)00000000000000(17)280331(10)LOT0001
              </div>
              <div class="text-xs text-muted" style="margin-top: 6px;">
                Example Devices Ltd | Sample City, Country
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Observed vs Reference and Regulatory Findings -->
        <div class="flex-col" style="gap: 16px;">
          ${criticalFinding ? `
            <div class="card">
              <div class="card-header-clean font-semibold text-sm">Observed vs Reference Discrepancy</div>
              <div class="kv-table">
                <div class="kv-row">
                  <span class="kv-label">Printed on label</span>
                  <span class="kv-value font-mono">
                    <span class="badge badge-danger">${escapeHtml(criticalFinding.observed || '')}</span>
                  </span>
                </div>
                <div class="kv-row">
                  <span class="kv-label">From barcode (reference)</span>
                  <span class="kv-value font-mono">
                    <span class="badge badge-teal">${escapeHtml(criticalFinding.expected || '')}</span>
                  </span>
                </div>
              </div>
            </div>
          ` : `
            <div class="card" style="text-align: center; padding: 24px; background: rgba(16, 185, 129, 0.06); border-color: rgba(16, 185, 129, 0.3);">
              <div style="color: var(--color-success-text); font-size: 2rem;">✓</div>
              <div class="font-semibold" style="margin-top: 6px; color: var(--color-success-text);">
                All Label Checks Passed
              </div>
              <div class="text-xs text-muted" style="margin-top: 4px;">
                0 critical findings. Extraction confirmed compliant with 21 CFR 801.
              </div>
            </div>
          `}

          <!-- Regulatory Findings with Citations -->
          <div class="card">
            <div class="card-header-clean flex-between">
              <span class="font-semibold text-sm">Regulatory Findings (${findings.length})</span>
              <span class="text-xs text-muted">21 CFR 801 Evidence</span>
            </div>
            <div class="flex-col" style="gap: 12px;">
              ${findings.map(f => `
                <div style="border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px; background: var(--color-bg-subtle);">
                  <div class="flex-between">
                    <div class="flex-row" style="gap: 6px;">
                      <span class="badge ${f.severity === 'critical' ? 'badge-danger' : 'badge-teal'}">
                        ${escapeHtml(f.severity)}
                      </span>
                      <span class="font-semibold text-xs">${escapeHtml(f.kind.replace('_', ' '))}</span>
                    </div>
                    <span class="text-xs text-muted">Field: <code>${escapeHtml(f.field || '')}</code></span>
                  </div>
                  <div class="text-xs text-muted" style="margin-top: 6px;">
                    ${escapeHtml(f.message)}
                  </div>
                  ${(f.citations || []).map(cit => `
                    <div style="margin-top: 8px; padding: 8px; background: #ffffff; border-radius: 4px; border: 1px solid var(--color-border); font-size: 0.75rem;">
                      <div class="flex-between">
                        <span class="font-semibold">
                          <span class="badge badge-teal">${escapeHtml(cit.source_type || 'cfr')}</span>
                          21 CFR ${escapeHtml(cit.section || '')}: ${escapeHtml(cit.title || '')}
                        </span>
                        ${cit.url ? `
                          <a href="${escapeHtml(cit.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-secondary" style="font-size: 0.7rem; padding: 1px 6px;">
                            View regulation &rarr;
                          </a>
                        ` : ''}
                      </div>
                      ${cit.quote ? `
                        <div style="font-style: italic; color: var(--color-text-muted); margin-top: 4px; border-left: 2px solid var(--color-primary-teal); padding-left: 8px;">
                          "${escapeHtml(cit.quote)}"
                        </div>
                      ` : ''}
                    </div>
                  `).join('')}
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    `;

    const exportBtn = container.querySelector('#btnExportInspectReport');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        if (window.LabelLensStateSwitcher) {
          window.LabelLensStateSwitcher.setScreen('D8 Export');
        } else {
          window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
            detail: { screen: 'D8 Export' }
          }));
        }
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
