/**
 * ui/js/render-d1.js
 * Renderer for Screen D1: Products
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Test identifiers labelled TEST.
 * - Never invent data. All values come from mock.
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

  function renderScreenD1(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    // 1. Single Product Detail View (professional/product_detail/success.json)
    if (safeData.product && safeData.record && safeData.templates) {
      const prod = safeData.product || {};
      const rec = safeData.record || {};
      const templates = safeData.templates || [];
      const labels = safeData.labels || [];
      const extra = rec.extra || {};
      const testBadge = renderTestBadge(rec.udi_di) || renderTestBadge(rec);

      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 20px; align-items: flex-start;">
          <div>
            <div class="flex-row" style="gap: 8px;">
              <h2>${escapeHtml(rec.name || 'Product Details')}</h2>
              ${testBadge}
              <span class="badge badge-blue">v${escapeHtml(String(prod.current_version || rec.version || 1))}</span>
            </div>
            <div class="text-xs text-muted" style="margin-top: 4px;">
              Model: <strong>${escapeHtml(rec.model || '')}</strong> | Product ID: <code>${escapeHtml(prod.product_id || '')}</code> | Market: ${(prod.intended_market || []).map(escapeHtml).join(', ')}
            </div>
          </div>
          <button class="btn btn-sm btn-secondary" type="button" id="btnBackToProductList">
            &larr; Back to Products
          </button>
        </div>

        <div class="grid-two-col">
          <!-- Specifications Card -->
          <div class="card">
            <div class="card-header-clean font-semibold text-sm">Product Specifications</div>
            <div class="kv-table">
              <div class="kv-row">
                <span class="kv-label">Primary UDI-DI</span>
                <span class="kv-value">
                  <code>${escapeHtml(rec.udi_di || 'none')}</code> ${renderTestBadge(rec.udi_di)}
                </span>
              </div>
              <div class="kv-row">
                <span class="kv-label">Manufacturer</span>
                <span class="kv-value">${escapeHtml(rec.manufacturer || '')}</span>
              </div>
              <div class="kv-row">
                <span class="kv-label">Manufacturer Address</span>
                <span class="kv-value">${escapeHtml(rec.manufacturer_address || '')}</span>
              </div>
              <div class="kv-row">
                <span class="kv-label">Sterilization</span>
                <span class="kv-value">${escapeHtml(rec.sterilization || 'Not specified')}</span>
              </div>
              <div class="kv-row">
                <span class="kv-label">Storage Conditions</span>
                <span class="kv-value">${escapeHtml(rec.storage || 'Not specified')}</span>
              </div>
              ${extra.lot ? `
                <div class="kv-row">
                  <span class="kv-label">Lot / Batch</span>
                  <span class="kv-value"><code>${escapeHtml(extra.lot)}</code></span>
                </div>
              ` : ''}
              ${extra.expiry ? `
                <div class="kv-row">
                  <span class="kv-label">Expiry Date</span>
                  <span class="kv-value font-mono">${escapeHtml(extra.expiry)}</span>
                </div>
              ` : ''}
              ${extra.serial ? `
                <div class="kv-row">
                  <span class="kv-label">Serial Number</span>
                  <span class="kv-value font-mono">${escapeHtml(extra.serial)}</span>
                </div>
              ` : ''}
            </div>
          </div>

          <!-- Associated Templates and Labels Card -->
          <div class="flex-col" style="gap: 16px;">
            <div class="card">
              <div class="card-header-clean flex-between">
                <span class="font-semibold text-sm">Registered Templates (${templates.length})</span>
                <span class="badge badge-teal">Deterministic Layout</span>
              </div>
              <div class="flex-col" style="gap: 10px;">
                ${templates.map(tpl => `
                  <div style="border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px; background: var(--color-bg-subtle);">
                    <div class="flex-between">
                      <div>
                        <div class="font-semibold text-sm"><code>${escapeHtml(tpl.template_id)}</code></div>
                        <div class="text-xs text-muted" style="margin-top: 2px;">
                          Dimensions: ${tpl.size_mm ? `${tpl.size_mm.w} x ${tpl.size_mm.h} mm` : ''} | Slots: ${(tpl.slots || []).length}
                        </div>
                      </div>
                      <button class="btn btn-sm btn-secondary" type="button" data-nav-screen="D2 Template setup">
                        View Template &rarr;
                      </button>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>

            <div class="card">
              <div class="card-header-clean flex-between">
                <span class="font-semibold text-sm">Associated Labels (${labels.length})</span>
                <span class="badge badge-purple">Versioned Artifacts</span>
              </div>
              <div class="flex-col" style="gap: 10px;">
                ${labels.map(lbl => `
                  <div style="border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px; background: var(--color-bg-subtle);">
                    <div class="flex-between">
                      <div>
                        <div class="font-semibold text-sm"><code>${escapeHtml(lbl.version_id)}</code></div>
                        <div class="text-xs text-muted" style="margin-top: 2px;">
                          Status: <span class="badge badge-teal">${escapeHtml(lbl.status || 'draft')}</span> | Kind: ${escapeHtml(lbl.kind || 'uploaded')}
                        </div>
                      </div>
                      <button class="btn btn-sm btn-primary" type="button" data-nav-screen="D4 Inspect">
                        Inspect &rarr;
                      </button>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
        </div>
      `;

      const backBtn = container.querySelector('#btnBackToProductList');
      if (backBtn) {
        backBtn.addEventListener('click', () => {
          if (window.LabelLensStateSwitcher) {
            window.LabelLensStateSwitcher.setScreen('D1 Products', 'success');
          } else {
            window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
              detail: { screen: 'D1 Products', state: 'success' }
            }));
          }
        });
      }

      container.querySelectorAll('[data-nav-screen]').forEach(btn => {
        btn.addEventListener('click', () => {
          const targetScreen = btn.dataset.navScreen;
          if (window.LabelLensStateSwitcher) {
            window.LabelLensStateSwitcher.setScreen(targetScreen);
          } else {
            window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
              detail: { screen: targetScreen }
            }));
          }
        });
      });
      return;
    }

    // 2. Empty State (professional/products/empty.json)
    const items = safeData.items || [];
    if (state === 'empty' || items.length === 0) {
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 20px;">
          <div>
            <h2>Products</h2>
            <div class="text-xs text-muted">Medical device product families and active label versions.</div>
          </div>
        </div>
        <div class="card" style="text-align: center; padding: 48px 24px; max-width: 640px; margin: 0 auto;">
          <div style="font-size: 2.2rem; margin-bottom: 12px; color: var(--color-text-muted);">📦</div>
          <h3>No products registered yet</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">
            Register your first medical device product family to manage label versions, deterministic templates, and regulatory compliance checks.
          </p>
        </div>
      `;
      return;
    }

    // 3. Product List State (professional/products/success.json)
    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 20px;">
        <div>
          <h2>Products (${items.length})</h2>
          <div class="text-xs text-muted">Device product families, active specifications, and open findings.</div>
        </div>
        <button class="btn btn-sm btn-secondary" type="button" id="btnInspectActiveProduct">
          Inspect Active Device &rarr;
        </button>
      </div>

      <div class="flex-col" style="gap: 16px;">
        ${items.map(item => {
          const prod = item.product || {};
          const rec = item.record || {};
          const testBadge = renderTestBadge(rec.udi_di) || renderTestBadge(rec);
          const hasOpenFindings = item.open_findings > 0;

          return `
            <div class="card" style="border: 1px solid var(--color-border); padding: 18px;">
              <div class="flex-between" style="align-items: flex-start;">
                <div>
                  <div class="flex-row" style="gap: 8px;">
                    <span class="font-semibold" style="font-size: 1.05rem;">${escapeHtml(rec.name || 'Unnamed Product')}</span>
                    ${testBadge}
                    <span class="badge badge-blue">v${escapeHtml(String(prod.current_version || rec.version || 1))}</span>
                    ${hasOpenFindings ? `
                      <span class="badge badge-warning">${item.open_findings} open finding(s)</span>
                    ` : `
                      <span class="badge badge-teal">Clean</span>
                    `}
                  </div>
                  <div class="text-xs text-muted" style="margin-top: 6px;">
                    ID: <code>${escapeHtml(prod.product_id || '')}</code> | Model: <strong>${escapeHtml(rec.model || 'none')}</strong> | Manufacturer: ${escapeHtml(rec.manufacturer || '')}
                  </div>
                  <div class="text-xs text-muted" style="margin-top: 4px;">
                    UDI-DI: <code>${escapeHtml(rec.udi_di || 'none')}</code> | Sterilization: ${escapeHtml(rec.sterilization || 'none')} | Labels: <strong>${item.label_count || 0}</strong>
                  </div>
                </div>

                <div class="flex-row" style="gap: 10px;">
                  <button class="btn btn-sm btn-secondary btn-view-product-detail" type="button" data-product-id="${escapeHtml(prod.product_id)}">
                    Product Details &rarr;
                  </button>
                  <button class="btn btn-sm btn-primary btn-inspect-product" type="button" data-product-id="${escapeHtml(prod.product_id)}">
                    Inspect
                  </button>
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    // View details button switches to product_detail state
    container.querySelectorAll('.btn-view-product-detail').forEach(btn => {
      btn.addEventListener('click', () => {
        if (window.LabelLensStateSwitcher) {
          window.LabelLensStateSwitcher.setScreen('D1 Products', 'success (product detail)');
        }
      });
    });

    // Inspect button routes to D4 Inspect
    container.querySelectorAll('.btn-inspect-product').forEach(btn => {
      btn.addEventListener('click', () => {
        if (window.LabelLensStateSwitcher) {
          window.LabelLensStateSwitcher.setScreen('D4 Inspect');
        } else {
          window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
            detail: { screen: 'D4 Inspect' }
          }));
        }
      });
    });

    const inspectActiveBtn = container.querySelector('#btnInspectActiveProduct');
    if (inspectActiveBtn) {
      inspectActiveBtn.addEventListener('click', () => {
        if (window.LabelLensStateSwitcher) {
          window.LabelLensStateSwitcher.setScreen('D4 Inspect');
        } else {
          window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
            detail: { screen: 'D4 Inspect' }
          }));
        }
      });
    }
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D1 Products'] = renderScreenD1;
  window.LabelLensRenderers['D1'] = renderScreenD1;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD1 };
  }
})();
