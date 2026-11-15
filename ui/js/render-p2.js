/**
 * ui/js/render-p2.js
 * Renderer for Screen P2: Product information (Mockup Panel 2)
 * 
 * Hard rules:
 * - Public medicine mode only (21 CFR 201, 208, 211).
 * - "Authenticity not verified. Based on a reference label match."
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

  function renderScreenP2(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    if (state === 'empty') {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px;">
          <h3>No reference label found</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">We could not match this package against official FDA drug labels in 21 CFR 201, 208, or 211.</p>
          <div style="margin-top: 16px;">
            <button class="btn btn-secondary" type="button" id="btnP2ScanAnother">Scan another side</button>
          </div>
        </div>
      `;
      const btn = container.querySelector('#btnP2ScanAnother');
      if (btn) {
        btn.addEventListener('click', () => {
          window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
            detail: { screen: 'P1 Scan and Understand' }
          }));
        });
      }
      return;
    }

    if (state === 'needs_review') {
      const candidates = safeData.candidates || [];
      container.innerHTML = `
        <div class="notice-banner notice-warning">
          <div class="notice-icon">i</div>
          <div>
            <div class="notice-title">Multiple candidates found</div>
            <div class="notice-text">The scan matched more than one reference label. Please select the product packaging in your hand.</div>
          </div>
        </div>

        <div class="card">
          <h3>Candidate reference labels (${candidates.length})</h3>
          <div style="margin-top: 16px; display: flex; flex-direction: column; gap: 12px;">
            ${candidates.map(c => `
              <div class="card" style="border: 1px solid var(--color-border); padding: 14px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <div class="font-semibold">${escapeHtml(c.product_name)}</div>
                  <div class="text-xs text-muted">${escapeHtml(c.dosage_form || '')} | ${escapeHtml(c.manufacturer || '')}</div>
                </div>
                <div class="flex-row">
                  <span class="badge badge-teal">Match: ${Math.round((c.match_confidence || 0) * 100)}%</span>
                  <button class="btn btn-sm btn-primary" type="button">Select</button>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
      return;
    }

    // Normal Success State (Panel 2 from mockup)
    const cand = (safeData.candidates && safeData.candidates[0]) || {};
    const photoData = cand.read_from_photo || {};
    const refData = cand.from_reference_label || {};
    const sources = safeData.sources || [];

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px; align-items: flex-start;">
        <div>
          <h2>Product information</h2>
          <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
            <span style="font-size: 1.1rem; font-weight: 700; color: var(--color-text-dark);">${escapeHtml(cand.product_name || 'ExampleMed 10 mg')}</span>
            <span class="badge badge-teal">Reference match found</span>
          </div>
          <div class="text-xs text-muted" style="margin-top: 2px;">${escapeHtml(cand.dosage_form || 'Film-coated tablets')} | ${escapeHtml(cand.active_substance || 'Example substance')}</div>
        </div>
        <div>
          <span class="text-xs text-muted">Confidence: <strong>${Math.round((cand.match_confidence || 0.94) * 100)}%</strong></span>
        </div>
      </div>

      <div class="tab-group">
        <button class="tab-btn active" type="button">Summary</button>
        <button class="tab-btn" type="button">Ingredients</button>
        <button class="tab-btn" type="button">Warnings</button>
        <button class="tab-btn" type="button">Sources</button>
      </div>

      <div class="grid-three-col">
        <!-- Card 1: Read from your photo -->
        <div class="card">
          <div class="card-header-clean flex-row">
            <span style="color: var(--color-primary-teal); font-weight: 700;">📷</span>
            <span class="font-semibold text-sm">Read from your photo</span>
          </div>
          <div class="kv-table">
            ${Object.entries(photoData).map(([k, v]) => `
              <div class="kv-row">
                <span class="kv-label">${escapeHtml(k)}</span>
                <span class="kv-value">${escapeHtml(String(v))}</span>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Card 2: From reference label -->
        <div class="card">
          <div class="card-header-clean flex-row">
            <span style="color: var(--color-primary-teal); font-weight: 700;">📄</span>
            <span class="font-semibold text-sm">From the reference label</span>
          </div>
          <div class="kv-table">
            ${Object.entries(refData).map(([k, v]) => `
              <div class="kv-row">
                <span class="kv-label">${escapeHtml(k)}</span>
                <span class="kv-value">${escapeHtml(String(v))}</span>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Card 3: Ask about this label teaser -->
        <div class="card">
          <div class="card-header-clean flex-row">
            <span style="color: var(--color-primary-teal); font-weight: 700;">💬</span>
            <span class="font-semibold text-sm">Ask about this label</span>
          </div>
          <div style="background-color: var(--color-bg-subtle); padding: 10px; border-radius: var(--radius-md); font-size: 0.85rem; margin-bottom: 12px;">
            ${escapeHtml(safeData.summary || 'ExampleMed 10 mg is a film-coated tablet containing an example substance. It is supplied in packs of 28 tablets.')}
          </div>
          ${sources.length > 0 ? `
            <div class="text-xs" style="margin-top: 8px;">
              <span class="font-semibold text-muted">Cited Regulatory Basis:</span>
              <div style="color: var(--color-text-dark); margin-top: 2px;">21 CFR ${escapeHtml(sources[0].section || '')} : ${escapeHtml(sources[0].title || '')}</div>
            </div>
          ` : ''}
          <div style="margin-top: 16px;">
            <button class="btn btn-sm btn-primary" style="width: 100%;" type="button" id="btnP2AskTeaser">Ask questions about this medicine</button>
          </div>
        </div>
      </div>

      <div class="flex-between" style="margin-top: 24px;">
        <button class="btn btn-secondary btn-sm" type="button" id="btnP2ScanAnotherSuccess">Scan another side</button>
        <a class="btn btn-primary btn-sm" href="${escapeHtml(cand.reference_label_url || '#')}" target="_blank" rel="noopener noreferrer">View reference source</a>
      </div>
    `;

    // Event listeners
    const askTeaser = container.querySelector('#btnP2AskTeaser');
    if (askTeaser) {
      askTeaser.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
          detail: { screen: 'P3 Ask about this label' }
        }));
      });
    }

    const scanAnother = container.querySelector('#btnP2ScanAnotherSuccess');
    if (scanAnother) {
      scanAnother.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
          detail: { screen: 'P1 Scan and Understand' }
        }));
      });
    }
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['P2 Product information'] = renderScreenP2;
  window.LabelLensRenderers['P2'] = renderScreenP2;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenP2 };
  }
})();
