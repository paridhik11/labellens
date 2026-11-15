/**
 * ui/js/render-d9.js
 * Renderer for Screen D9: History (Audit Log and Versions)
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Fixed audit trail: immutable events.
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

  function renderScreenD9(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};
    const items = safeData.items || [];

    // Empty State
    if (state === 'empty' || items.length === 0) {
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Product History &amp; Audit Trail</h2>
            <div class="text-xs text-muted">Immutable regulatory event log.</div>
          </div>
        </div>
        <div class="card" style="text-align: center; padding: 48px;">
          <h3>No audit events recorded</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">No lifecycle events exist for this product family yet.</p>
        </div>
      `;
      return;
    }

    // Label versions list view
    if (safeData.versions || (items[0] && items[0].version_id)) {
      const versions = safeData.versions || items;
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Label Versions History</h2>
            <div class="text-xs text-muted">Product: <code>${escapeHtml(safeData.product_id || 'prd_exampledevice')}</code></div>
          </div>
        </div>

        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Registered Versions (${versions.length})</div>
          <div class="kv-table">
            ${versions.map(v => `
              <div class="kv-row" style="padding: 12px 0;">
                <div>
                  <div class="font-semibold text-sm">${escapeHtml(v.version_id)}</div>
                  <div class="text-xs text-muted">Created: ${escapeHtml(v.created_at || '')} by <code>${escapeHtml(v.created_by || 'user')}</code></div>
                </div>
                <div class="flex-row">
                  <span class="badge ${v.status === 'published' ? 'badge-teal' : (v.status === 'draft' ? 'badge-draft' : 'badge-blue')}">
                    ${escapeHtml(v.status || 'active')}
                  </span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
      return;
    }

    // Standard Audit Event Log View
    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Audit Trail : ${escapeHtml(safeData.product_id || 'prd_exampledevice')}</h2>
          <div class="text-xs text-muted">21 CFR 820.181 Device Master Record &amp; 21 CFR 11 Audit Trail</div>
        </div>
        <span class="badge badge-teal">${items.length} Event(s)</span>
      </div>

      <div class="card">
        <div class="card-header-clean font-semibold text-sm">Recorded Regulatory Events</div>
        <div class="flex-col" style="gap: 12px;">
          ${items.map(evt => `
            <div class="card" style="border: 1px solid var(--color-border); padding: 12px;">
              <div class="flex-between">
                <span class="font-semibold text-sm" style="color: var(--color-primary-blue);">
                  ${escapeHtml(evt.action || 'event')}
                </span>
                <span class="text-xs text-muted">${escapeHtml(evt.at || '')}</span>
              </div>
              <div class="text-xs text-muted" style="margin-top: 4px;">
                User: <code>${escapeHtml(evt.user_id || 'system')}</code> | Entity: <code>${escapeHtml(evt.entity_type || '')}</code> (${escapeHtml(evt.entity_id || '')})
                ${evt.version_before && evt.version_after ? ` | Version: v${evt.version_before} &rarr; v${evt.version_after}` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D9 History'] = renderScreenD9;
  window.LabelLensRenderers['D9'] = renderScreenD9;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD9 };
  }
})();
