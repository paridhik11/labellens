/**
 * ui/js/render-d1.js
 * Renderer for Screen D1: Products
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

  function renderScreenD1(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    // Single product detail view
    if (safeData.product_id && !safeData.items) {
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>${escapeHtml(safeData.name || 'Product Details')}</h2>
            <div class="text-xs text-muted">Product ID: ${escapeHtml(safeData.product_id)} | Created: ${escapeHtml(safeData.created_at || '')}</div>
          </div>
          <button class="btn btn-sm btn-secondary" type="button" id="btnBackToProducts">Back to Products</button>
        </div>

        <div class="grid-two-col">
          <div class="card">
            <div class="card-header-clean font-semibold text-sm">Product Specifications</div>
            <div class="kv-table">
              <div class="kv-row">
                <span class="kv-label">Primary UDI-DI</span>
                <span class="kv-value"><span class="badge badge-test">${escapeHtml(safeData.primary_di || '00000000000000 [TEST]')}</span></span>
              </div>
              <div class="kv-row">
                <span class="kv-label">Classification</span>
                <span class="kv-value">${escapeHtml(safeData.classification || 'Class II')}</span>
              </div>
              <div class="kv-row">
                <span class="kv-label">Sterilization</span>
                <span class="kv-value">${escapeHtml(safeData.sterilization || 'EO')}</span>
              </div>
              <div class="kv-row">
                <span class="kv-label">Description</span>
                <span class="kv-value">${escapeHtml(safeData.description || '')}</span>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-header-clean flex-between">
              <span class="font-semibold text-sm">Associated Labels</span>
              <span class="badge badge-teal">${(safeData.labels || []).length} label(s)</span>
            </div>
            <div class="flex-col" style="gap: 8px;">
              ${(safeData.labels || []).map(lbl => `
                <div class="card" style="border: 1px solid var(--color-border); padding: 10px; display: flex; justify-content: space-between; align-items: center;">
                  <div>
                    <div class="font-semibold text-sm">${escapeHtml(lbl.name || lbl.label_id)}</div>
                    <div class="text-xs text-muted">Kind: ${escapeHtml(lbl.kind || 'carton')} | Active: ${escapeHtml(lbl.active_version_id || 'L2')}</div>
                  </div>
                  <button class="btn btn-sm btn-primary" type="button" data-inspect-label="${escapeHtml(lbl.label_id)}">Inspect</button>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      `;

      const backBtn = container.querySelector('#btnBackToProducts');
      if (backBtn) {
        backBtn.addEventListener('click', () => {
          if (window.LabelLensStateSwitcher) {
            window.LabelLensStateSwitcher.setScreen('D1 Products', 'success');
          }
        });
      }

      container.querySelectorAll('[data-inspect-label]').forEach(btn => {
        btn.addEventListener('click', () => {
          window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
            detail: { screen: 'D4 Inspect' }
          }));
        });
      });
      return;
    }

    // List of products
    const products = safeData.items || [];
    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Products</h2>
          <div class="text-xs text-muted">Medical device product families and active label versions.</div>
        </div>
        <button class="btn btn-sm btn-primary" type="button">+ Register product</button>
      </div>

      ${products.length === 0 ? `
        <div class="card" style="text-align: center; padding: 48px;">
          <h3>No products registered yet</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">Register your first medical device product family to manage label versions and templates.</p>
        </div>
      ` : `
        <div class="card">
          <div class="kv-table">
            ${products.map(p => `
              <div class="kv-row" style="padding: 12px 0;">
                <div>
                  <div class="font-semibold">${escapeHtml(p.name)}</div>
                  <div class="text-xs text-muted">ID: ${escapeHtml(p.product_id)} | Primary UDI-DI: <span class="badge badge-test">${escapeHtml(p.primary_di || '00000000000000 [TEST]')}</span></div>
                </div>
                <div class="flex-row">
                  <span class="badge badge-teal">${p.label_count || 1} labels</span>
                  <button class="btn btn-sm btn-secondary" type="button" data-nav-inspect="D4 Inspect">Inspect</button>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `}
    `;

    container.querySelectorAll('[data-nav-inspect]').forEach(btn => {
      btn.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
          detail: { screen: 'D4 Inspect' }
        }));
      });
    });
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D1 Products'] = renderScreenD1;
  window.LabelLensRenderers['D1'] = renderScreenD1;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD1 };
  }
})();
