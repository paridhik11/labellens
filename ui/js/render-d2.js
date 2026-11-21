/**
 * ui/js/render-d2.js
 * Renderer for Screen D2: Template setup (Draw and name slots)
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Mark drafts clearly: prominent DRAFT watermark/badge and disclaimer:
 *   "Draft generated for review. Not a compliance determination."
 * - Never invent data. Every value on screen comes from a mock.
 * - Test identifiers labelled TEST.
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

  function renderStateD2(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    const draftDisclaimer = safeData.disclaimer || 'Draft generated for review. Not a compliance determination.';

    // 1. Failed Check State (professional/template_setup/failed_check.json)
    if (state === 'failed_check' || safeData.passed === false) {
      const findings = safeData.findings || [];
      const criticalCount = safeData.critical_count || 1;
      const reviewCount = safeData.review_count || 0;

      container.innerHTML = `
        <!-- Draft Review Banner -->
        <div class="notice-banner notice-warning" style="margin-bottom: 16px;">
          <div class="notice-icon">i</div>
          <div style="flex: 1;">
            <div class="flex-between">
              <span class="notice-title">DRAFT TEMPLATE SPECIFICATION</span>
              <span class="badge badge-draft">DRAFT</span>
            </div>
            <div class="notice-text" style="margin-top: 4px;">
              ${escapeHtml(draftDisclaimer)}
            </div>
          </div>
        </div>

        <div class="flex-between" style="margin-bottom: 20px; align-items: flex-start;">
          <div>
            <div class="flex-row" style="gap: 8px;">
              <h2>Template validation failed</h2>
              <span class="badge badge-danger">Layout Violations</span>
            </div>
            <div class="text-xs text-muted" style="margin-top: 4px;">
              Template ID: <code>${escapeHtml(safeData.template_id || 'tpl_exampledevice_carton')}</code> | Check ID: <code>${escapeHtml(safeData.check_id || 'chk_tpl_0001')}</code>
            </div>
          </div>
          <button class="btn btn-sm btn-secondary" type="button" id="btnRetryTemplateCheck">
            Re-run Validation &rarr;
          </button>
        </div>

        <div class="notice-banner notice-danger" style="margin-bottom: 20px;">
          <div class="notice-icon">!</div>
          <div style="flex: 1;">
            <div class="notice-title">
              ${criticalCount} Critical Finding(s), ${reviewCount} Review Finding(s)
            </div>
            <div class="notice-text" style="margin-top: 4px;">
              Template layout violates deterministic design rules. Reserved draft band overlap or bounding box collisions must be resolved.
            </div>
          </div>
        </div>

        <div class="grid-two-col">
          <!-- Visual Canvas highlighting collisions -->
          <div class="card">
            <div class="card-header-clean flex-between">
              <span class="font-semibold text-sm">Collisions on 100 x 60 mm Canvas</span>
              <span class="badge badge-danger">2 collisions</span>
            </div>

            <div style="background: #ffffff; border: 2px solid #ef4444; border-radius: var(--radius-md); position: relative; height: 260px; overflow: hidden; box-shadow: inset 0 0 10px rgba(239, 68, 68, 0.1);">
              <!-- Reserved Draft Band (Top 9mm) -->
              <div style="position: absolute; top: 0; left: 0; right: 0; height: 36px; background: rgba(239, 68, 68, 0.15); border-bottom: 2px dashed #ef4444; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 0.7rem; font-weight: 800; color: #dc2626; letter-spacing: 1px;">
                  RESERVED DRAFT WATERMARK BAND (TOP 9 MM)
                </span>
              </div>

              <!-- Overlapping slot 'name' placed at y=2mm -->
              <div style="position: absolute; top: 8px; left: 20px; width: 180px; height: 32px; border: 2px solid #dc2626; background: rgba(254, 226, 226, 0.85); border-radius: 4px; padding: 4px 8px; font-size: 0.75rem;">
                <div style="font-weight: 700; color: #b91c1c;">Slot: name [CRITICAL]</div>
                <div style="font-size: 0.65rem; color: #7f1d1d;">y = 2 mm (must be &gt;= 9 mm)</div>
              </div>

              <!-- Overlapping slots 'lot' and 'udi_barcode' -->
              <div style="position: absolute; top: 120px; right: 30px; width: 120px; height: 75px; border: 2px dashed #f59e0b; background: rgba(254, 243, 199, 0.7); border-radius: 4px; padding: 6px; font-size: 0.72rem;">
                <div style="font-weight: 700; color: #b45309;">Overlap Collision</div>
                <div style="font-size: 0.65rem; color: #78350f; margin-top: 2px;">Slots 'lot' and 'udi_barcode' overlap bounding boxes</div>
              </div>
            </div>
          </div>

          <!-- Finding Details List -->
          <div class="card">
            <div class="card-header-clean font-semibold text-sm">Layout Findings (${findings.length})</div>
            <div class="flex-col" style="gap: 12px;">
              ${findings.map(f => `
                <div style="border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 14px; background: var(--color-bg-subtle);">
                  <div class="flex-between">
                    <span class="font-semibold text-sm" style="color: ${f.severity === 'critical' ? 'var(--color-danger-text)' : 'inherit'};">
                      ${escapeHtml(f.kind.replace('_', ' '))} &rarr; <code>${escapeHtml(f.field || 'layout')}</code>
                    </span>
                    <span class="badge ${f.severity === 'critical' ? 'badge-danger' : 'badge-warning'}">${escapeHtml(f.severity)}</span>
                  </div>
                  <div class="text-sm text-muted" style="margin-top: 6px;">
                    ${escapeHtml(f.message)}
                  </div>
                  ${(f.observed || f.expected) ? `
                    <div class="text-xs font-mono" style="margin-top: 8px; padding: 4px 8px; background: #ffffff; border-radius: 4px; border: 1px solid var(--color-border);">
                      Observed: <strong>${escapeHtml(f.observed)}</strong> | Expected: <strong>${escapeHtml(f.expected)}</strong>
                    </div>
                  ` : ''}
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      `;

      const retryBtn = container.querySelector('#btnRetryTemplateCheck');
      if (retryBtn) {
        retryBtn.addEventListener('click', () => {
          if (window.LabelLensStateSwitcher) {
            window.LabelLensStateSwitcher.setScreen('D2 Template setup', 'success');
          }
        });
      }
      return;
    }

    // 2. Success State (professional/template_setup/success.json)
    const slots = safeData.slots || [];
    const size = safeData.size_mm || { w: 100, h: 60 };

    container.innerHTML = `
      <!-- Draft Review Banner -->
      <div class="notice-banner notice-warning" style="margin-bottom: 16px;">
        <div class="notice-icon">i</div>
        <div style="flex: 1;">
          <div class="flex-between">
            <span class="notice-title">DRAFT TEMPLATE SPECIFICATION</span>
            <span class="badge badge-draft">DRAFT</span>
          </div>
          <div class="notice-text" style="margin-top: 4px;">
            ${escapeHtml(draftDisclaimer)}
          </div>
        </div>
      </div>

      <div class="flex-between" style="margin-bottom: 20px; align-items: flex-start;">
        <div>
          <div class="flex-row" style="gap: 8px;">
            <h2>Template: <code>${escapeHtml(safeData.template_id || 'tpl_exampledevice_carton')}</code></h2>
            <span class="badge badge-teal">Registered v${escapeHtml(String(safeData.version || 1))}</span>
          </div>
          <div class="text-xs text-muted" style="margin-top: 4px;">
            Product: <code>${escapeHtml(safeData.product_id || '')}</code> | Dimensions: <strong>${size.w} x ${size.h} mm</strong> | Min font: ${safeData.min_font_pt || 6} pt | Background: <code>${escapeHtml(safeData.background || 'base.svg')}</code>
          </div>
        </div>
        <button class="btn btn-sm btn-primary" type="button" id="btnTestLayoutCheck">
          Run Layout Check &rarr;
        </button>
      </div>

      <div class="grid-two-col">
        <!-- Interactive Template Canvas at Physical Scale -->
        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Deterministic Slot Placement</span>
            <span class="badge badge-blue">Physical 100 x 60 mm</span>
          </div>

          <div style="background: #ffffff; border: 2px solid var(--color-border); border-radius: var(--radius-md); position: relative; height: 280px; overflow: hidden; box-shadow: var(--shadow-sm);">
            <!-- Reserved Draft Band (Top 9mm) -->
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 36px; background: rgba(124, 58, 237, 0.08); border-bottom: 1.5px dashed var(--color-draft-purple); display: flex; align-items: center; justify-content: center;">
              <span style="font-size: 0.68rem; font-weight: 800; color: var(--color-draft-purple); letter-spacing: 0.08em;">
                RESERVED DRAFT WATERMARK BAND (TOP 9 MM)
              </span>
            </div>

            <!-- Slots placed relative to 100mm width and 60mm height -->
            ${slots.map(s => {
              const bbox = s.bbox_mm || [0, 0, 10, 10];
              const leftPct = (bbox[0] / size.w) * 100;
              const topPct = (bbox[1] / size.h) * 100;
              const widthPct = (bbox[2] / size.w) * 100;
              const heightPct = (bbox[3] / size.h) * 100;
              const isBarcode = s.type === 'barcode';

              return `
                <div style="position: absolute; left: ${leftPct}%; top: ${topPct}%; width: ${widthPct}%; height: ${heightPct}%; border: 1.5px solid ${isBarcode ? '#0284c7' : '#0d9488'}; background: ${isBarcode ? 'rgba(2, 132, 199, 0.08)' : 'rgba(13, 148, 136, 0.06)'}; border-radius: 3px; padding: 2px 4px; overflow: hidden; font-size: 0.65rem;" title="${escapeHtml(s.id)} (${s.type}) [${bbox.join(', ')}]">
                  <div style="font-weight: 700; color: ${isBarcode ? '#0369a1' : '#0f766e'}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    ${escapeHtml(s.id)}
                  </div>
                  <div style="font-size: 0.58rem; color: #64748b; white-space: nowrap;">
                    ${escapeHtml(s.field)}
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>

        <!-- Defined Slots Table -->
        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Defined Slots (${slots.length})</span>
            <span class="text-xs text-muted">Author: <code>${escapeHtml(safeData.created_by || 'usr_demo_admin')}</code></span>
          </div>
          <div style="max-height: 280px; overflow-y: auto;">
            <div class="kv-table">
              ${slots.map(s => `
                <div class="kv-row" style="padding: 8px 0;">
                  <div>
                    <div class="font-semibold text-xs flex-row" style="gap: 6px;">
                      <span>${escapeHtml(s.id)}</span>
                      <span class="badge ${s.type === 'barcode' ? 'badge-blue' : s.type === 'symbol' ? 'badge-purple' : 'badge-teal'}" style="font-size: 0.65rem; padding: 1px 5px;">
                        ${escapeHtml(s.type)}
                      </span>
                    </div>
                    <div class="text-xs text-muted" style="margin-top: 2px;">
                      Target: <code>${escapeHtml(s.field)}</code> ${s.font ? `| ${escapeHtml(s.font)} ${s.size_pt}pt` : ''} ${s.symbology ? `| ${escapeHtml(s.symbology)}` : ''}
                    </div>
                  </div>
                  <span class="font-mono text-xs text-muted" style="font-size: 0.72rem;">
                    [${(s.bbox_mm || []).join(', ')}]
                  </span>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    `;

    const testCheckBtn = container.querySelector('#btnTestLayoutCheck');
    if (testCheckBtn) {
      testCheckBtn.addEventListener('click', () => {
        if (window.LabelLensStateSwitcher) {
          window.LabelLensStateSwitcher.setScreen('D2 Template setup', 'failed_check');
        }
      });
    }
  }

  /** In api mode a card on top registers the template shown (or pasted JSON) through the real endpoint. */
  function renderScreenD2(container, state, meta, data) {
    if (!container) return;
    if (window.LabelLensData.CONFIG.mode !== 'api') { renderStateD2(container, state, meta, data); return; }
    const d = data || {};
    const draft = d.slots ? { size_mm: d.size_mm, background: d.background, ...(d.min_font_pt ? { min_font_pt: d.min_font_pt } : {}), slots: d.slots } : null;
    const pid = (window.LabelLensData.CONFIG.ids || {}).product_id || d.product_id || '';
    const esc = escapeHtml;
    container.innerHTML = `
      <div class="card" style="margin-bottom: 16px;" data-testid="register-card">
        <div class="card-header-clean font-semibold text-sm">Register this template (live)</div>
        <label class="text-xs text-muted" for="d2Product">Product id</label><br>
        <input type="text" id="d2Product" value="${esc(pid)}" style="padding: 6px 8px; border: 1px solid var(--color-border); border-radius: var(--radius-md); width: 260px;">
        <textarea id="d2Json" rows="6" data-testid="d2-json" style="width: 100%; margin-top: 8px; font-family: monospace; font-size: 0.75rem;" placeholder='{"size_mm": {...}, "background": null, "slots": [...]}'>${draft ? esc(JSON.stringify(draft, null, 2)) : ''}</textarea>
        <div class="flex-row" style="gap: 8px; margin-top: 8px;"><button class="btn btn-primary btn-sm" type="button" id="btnRegisterTemplate">Register template</button></div>
        <div class="text-xs" id="d2Result" data-testid="d2-result" style="margin-top: 8px;"></div>
      </div>
      <div id="d2State"></div>`;
    renderStateD2(container.querySelector('#d2State'), state, meta, data);
    const out = container.querySelector('#d2Result');
    container.querySelector('#btnRegisterTemplate').addEventListener('click', async () => {
      let body;
      try { body = JSON.parse(container.querySelector('#d2Json').value); } catch (e) { out.textContent = 'The JSON is not valid: ' + e.message; return; }
      const product = container.querySelector('#d2Product').value.trim();
      if (!product) { out.textContent = 'A product id is required.'; return; }
      out.textContent = 'Registering...';
      try {
        const r = await window.LabelLensActions.registerTemplate(product, body);
        if (r.status === 201) {
          window.LabelLensData.setIds({ product_id: product });
          out.innerHTML = `Registered template <code>${esc(r.body.template_id)}</code> version ${esc(r.body.version)} (${esc(r.mock ? 'mock answer from the server' : 'stored')}).`;
        } else if (r.status === 422 && r.body && r.body.findings) {
          out.innerHTML = `Refused: ${r.body.findings.length} layout finding(s): ` + r.body.findings.map(f => esc(f.kind) + ' - ' + esc(f.message)).join('; ');
        } else {
          out.textContent = `Refused (HTTP ${r.status}): ${(r.body && (r.body.message || r.body.error)) || ''}`;
        }
      } catch (e) { out.textContent = 'Request failed: ' + e.message; }
    });
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D2 Template setup'] = renderScreenD2;
  window.LabelLensRenderers['D2'] = renderScreenD2;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD2 };
  }
})();
