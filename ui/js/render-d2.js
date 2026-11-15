/**
 * ui/js/render-d2.js
 * Renderer for Screen D2: Template setup
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Mark drafts clearly.
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

  function renderScreenD2(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    // Failed Check State (e.g. slot in DRAFT band, overlap)
    if (state === 'failed_check' || safeData.passed === false) {
      const findings = safeData.findings || [];
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Template validation failed</h2>
            <div class="text-xs text-muted">Template ID: <code>${escapeHtml(safeData.template_id || 'tpl_0001')}</code> | Check ID: <code>${escapeHtml(safeData.check_id || 'chk_tpl_0001')}</code></div>
          </div>
          <span class="badge badge-danger">Validation Failed</span>
        </div>

        <div class="notice-banner notice-danger">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">${safeData.critical_count || 1} Critical Finding(s), ${safeData.review_count || 0} Review Finding(s)</div>
            <div class="notice-text">Template layout violates deterministic design rules. Please resolve bounding box collisions before registration.</div>
          </div>
        </div>

        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Layout Findings (${findings.length})</div>
          <div class="flex-col" style="gap: 12px;">
            ${findings.map(f => `
              <div class="card" style="border: 1px solid var(--color-border); padding: 12px;">
                <div class="flex-between">
                  <span class="font-semibold text-sm" style="color: ${f.severity === 'critical' ? 'var(--color-danger-text)' : 'inherit'};">
                    ${escapeHtml(f.kind.replace('_', ' '))} (${escapeHtml(f.field || 'layout')})
                  </span>
                  <span class="badge ${f.severity === 'critical' ? 'badge-danger' : 'badge-warning'}">${escapeHtml(f.severity)}</span>
                </div>
                <div class="text-sm text-muted" style="margin-top: 4px;">${escapeHtml(f.message)}</div>
                ${f.observed ? `
                  <div class="text-xs" style="margin-top: 6px;">
                    Observed: <code>${escapeHtml(f.observed)}</code> | Expected: <code>${escapeHtml(f.expected)}</code>
                  </div>
                ` : ''}
              </div>
            `).join('')}
          </div>
        </div>
      `;
      return;
    }

    // Success State
    const slots = safeData.slots || [];
    const size = safeData.size_mm || { w: 100, h: 60 };

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Template setup: ${escapeHtml(safeData.template_id || 'tpl_exampledevice_carton')}</h2>
          <div class="text-xs text-muted">Product: <code>${escapeHtml(safeData.product_id || '')}</code> | Dimensions: ${size.w} x ${size.h} mm | Min font: ${safeData.min_font_pt || 6} pt</div>
        </div>
        <span class="badge badge-teal">Template Registered (v${safeData.version || 1})</span>
      </div>

      <div class="grid-two-col">
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Template Slot Layout</div>
          <div style="background: #f8fafc; border: 2px dashed #94a3b8; border-radius: var(--radius-md); padding: 16px; position: relative; min-height: 240px;">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 18px; background: rgba(124, 58, 237, 0.1); border-bottom: 1px dashed var(--color-draft-purple); font-size: 0.65rem; color: var(--color-draft-purple); text-align: center; line-height: 18px; font-weight: 700;">
              RESERVED DRAFT WATERMARK BAND
            </div>
            <div style="margin-top: 24px; display: flex; flex-direction: column; gap: 8px;">
              ${slots.map(s => `
                <div style="border: 1px solid #cbd5e1; background: #ffffff; padding: 6px 10px; border-radius: 4px; font-size: 0.75rem; display: flex; justify-content: space-between;">
                  <span class="font-semibold">${escapeHtml(s.id)} (${escapeHtml(s.type)})</span>
                  <span class="text-muted font-mono">[${(s.bbox_mm || []).join(', ')}]</span>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Defined Slots (${slots.length})</span>
            <span class="text-xs text-muted">Created by: ${escapeHtml(safeData.created_by || 'usr_demo_admin')}</span>
          </div>
          <div class="kv-table">
            ${slots.map(s => `
              <div class="kv-row" style="padding: 8px 0;">
                <div>
                  <div class="font-semibold text-xs">${escapeHtml(s.id)} &rarr; ${escapeHtml(s.field)}</div>
                  <div class="text-xs text-muted">${s.font || 'Helvetica'} ${s.size_pt ? s.size_pt + 'pt' : ''}</div>
                </div>
                <span class="badge badge-blue text-xs">${escapeHtml(s.type)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D2 Template setup'] = renderScreenD2;
  window.LabelLensRenderers['D2'] = renderScreenD2;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD2 };
  }
})();
