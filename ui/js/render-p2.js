/**
 * ui/js/render-p2.js
 * Renderer for Screen P2: Product information (Mockup Panel 2)
 * 
 * Hard rules:
 * - Public medicine mode only (21 CFR 201, 208, 211).
 * - "Authenticity not verified. Based on a reference label match."
 * - Never invent data. Every value on screen must come from a mock.
 * - If "Confidence: 94%" on P2 is not in the mock, remove it.
 * - Citations show regulation section, verbatim quote, and source type (cfr or label_section).
 * - Test identifiers show a visible TEST badge.
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

  function renderScreenP2(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    // 1. Empty State (public/product/empty.json)
    if (state === 'empty' || (Array.isArray(safeData.candidates) && safeData.candidates.length === 0)) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px 24px; max-width: 640px; margin: 0 auto;">
          <div style="font-size: 2.2rem; margin-bottom: 12px; color: var(--color-text-muted);">📑</div>
          <h3>No reference label found</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">
            We could not match this package against official FDA drug labels in 21 CFR 201, 208, or 211.
          </p>
          <div style="margin-top: 20px;">
            <button class="btn btn-secondary" type="button" id="btnP2ScanAnother">Scan another side</button>
          </div>
        </div>
      `;
      const btn = container.querySelector('#btnP2ScanAnother');
      if (btn) {
        btn.addEventListener('click', () => {
          if (window.LabelLensStateSwitcher) {
            window.LabelLensStateSwitcher.setScreen('P1 Scan and Understand', 'empty (idle)');
          } else {
            window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
              detail: { screen: 'P1 Scan and Understand' }
            }));
          }
        });
      }
      return;
    }

    // 2. Needs Review State (public/product/needs_review.json)
    if (state === 'needs_review') {
      const candidates = safeData.candidates || [];
      container.innerHTML = `
        <div class="notice-banner notice-warning">
          <div class="notice-icon">i</div>
          <div>
            <div class="notice-title">Multiple candidates found</div>
            <div class="notice-text">
              The scan matched more than one reference label. Please select the product packaging in your hand.
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header-clean flex-between">
            <h3>Candidate reference labels (${candidates.length})</h3>
            <span class="badge badge-warning">Disambiguation needed</span>
          </div>

          <div style="margin-top: 12px; display: flex; flex-direction: column; gap: 12px;">
            ${candidates.map((c, idx) => {
              const testBadge = renderTestBadge(c.product_id) || renderTestBadge(c);
              const hasConfidence = typeof c.match_confidence === 'number';
              const confDisplay = hasConfidence ? `Match: ${Math.round(c.match_confidence * 100)}%` : '';
              return `
                <div class="card" style="border: 1px solid var(--color-border); padding: 16px; display: flex; justify-content: space-between; align-items: center;">
                  <div>
                    <div class="flex-row" style="gap: 8px;">
                      <span class="font-semibold" style="font-size: 1rem;">${escapeHtml(c.product_name || '')}</span>
                      ${testBadge}
                    </div>
                    <div class="text-xs text-muted" style="margin-top: 4px;">
                      ${[c.dosage_form, c.active_substance, c.pack_size, c.manufacturer].filter(Boolean).map(escapeHtml).join(' | ')}
                    </div>
                  </div>
                  <div class="flex-row" style="gap: 12px;">
                    ${hasConfidence ? `<span class="badge badge-teal">${confDisplay}</span>` : ''}
                    <button class="btn btn-sm btn-primary btn-select-candidate" data-index="${idx}" type="button">
                      Select
                    </button>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>

        <div id="p2SelectedCandidateContainer" style="margin-top: 24px;"></div>
      `;

      // Allow candidate selection to preview candidate details
      const selectBtns = container.querySelectorAll('.btn-select-candidate');
      selectBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const idx = parseInt(btn.dataset.index, 10);
          const chosen = candidates[idx];
          if (chosen) {
            const detailContainer = container.querySelector('#p2SelectedCandidateContainer');
            if (detailContainer) {
              renderCandidateDetails(detailContainer, chosen, safeData.summary || '', safeData.sources || []);
              detailContainer.scrollIntoView({ behavior: 'smooth' });
            }
          }
        });
      });
      return;
    }

    // 3. Success State (public/product/success.json)
    const cand = (safeData.candidates && safeData.candidates[0]) || {};
    renderCandidateDetails(container, cand, safeData.summary || '', safeData.sources || []);
  }

  function renderCandidateDetails(container, cand, summaryText, sourcesList) {
    const photoData = cand.read_from_photo || {};
    const refData = cand.from_reference_label || {};
    const sources = sourcesList || [];

    // Confidence: only show when present in mock, remove otherwise
    const hasConfidence = typeof cand.match_confidence === 'number';
    const confidenceHtml = hasConfidence
      ? `<span class="text-xs text-muted">Confidence: <strong>${Math.round(cand.match_confidence * 100)}%</strong></span>`
      : '';

    const testBadge = renderTestBadge(cand.product_id) || renderTestBadge(cand);
    const subtitleParts = [cand.dosage_form, cand.active_substance, cand.pack_size].filter(Boolean);

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px; align-items: flex-start;">
        <div>
          <h2>Product information</h2>
          <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
            <span style="font-size: 1.15rem; font-weight: 700; color: var(--color-text-dark);">${escapeHtml(cand.product_name || '')}</span>
            <span class="badge badge-teal">Reference match found</span>
            ${testBadge}
          </div>
          ${subtitleParts.length > 0 ? `
            <div class="text-xs text-muted" style="margin-top: 2px;">
              ${subtitleParts.map(escapeHtml).join(' | ')}
            </div>
          ` : ''}
        </div>
        <div>
          ${confidenceHtml}
        </div>
      </div>

      <div class="tab-group" id="p2TabGroup">
        <button class="tab-btn active" data-tab="summary" type="button">Summary</button>
        <button class="tab-btn" data-tab="sources" type="button">Sources (${sources.length})</button>
      </div>

      <!-- Tab Content: Summary -->
      <div id="p2TabSummaryContent">
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
                  <span class="kv-value">${escapeHtml(String(v))} ${renderTestBadge(v)}</span>
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
                  <span class="kv-value">${escapeHtml(String(v))} ${renderTestBadge(v)}</span>
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
            ${summaryText ? `
              <div style="background-color: var(--color-bg-subtle); padding: 12px; border-radius: var(--radius-md); font-size: 0.85rem; margin-bottom: 12px; line-height: 1.45;">
                ${escapeHtml(summaryText)}
              </div>
            ` : ''}

            ${sources.length > 0 ? `
              <div class="text-xs" style="margin-top: 10px; border-top: 1px solid var(--color-border); padding-top: 10px;">
                <span class="font-semibold text-muted">Cited Regulatory Basis:</span>
                <div style="margin-top: 4px; display: flex; align-items: center; gap: 6px;">
                  <span class="badge badge-teal">${escapeHtml(sources[0].source_type || 'cfr')}</span>
                  <span style="font-weight: 600;">21 CFR ${escapeHtml(sources[0].section || '')}: ${escapeHtml(sources[0].title || '')}</span>
                </div>
                ${sources[0].quote ? `
                  <div style="margin-top: 6px; font-style: italic; color: var(--color-text-muted);">
                    "${escapeHtml(sources[0].quote)}"
                  </div>
                ` : ''}
              </div>
            ` : ''}

            <div style="margin-top: 16px;">
              <button class="btn btn-sm btn-primary" style="width: 100%;" type="button" id="btnP2AskTeaser">
                Ask questions about this medicine &rarr;
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab Content: Sources -->
      <div id="p2TabSourcesContent" style="display: none;">
        <div class="card">
          <div class="card-header-clean flex-between">
            <h3>Cited Regulatory Sources</h3>
            <span class="badge badge-teal">21 CFR Reference Corpus</span>
          </div>
          ${sources.length === 0 ? `
            <p class="text-sm text-muted">No external regulatory citations provided for this match.</p>
          ` : `
            <div style="display: flex; flex-direction: column; gap: 16px;">
              ${sources.map(s => `
                <div style="border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 16px; background-color: var(--color-bg-subtle);">
                  <div class="flex-between">
                    <div class="flex-row" style="gap: 8px;">
                      <span class="badge badge-teal">${escapeHtml(s.source_type || 'cfr')}</span>
                      <span class="font-semibold text-sm">21 CFR ${escapeHtml(s.section || '')}: ${escapeHtml(s.title || '')}</span>
                    </div>
                    ${s.url ? `
                      <a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-secondary">
                        View regulation &rarr;
                      </a>
                    ` : ''}
                  </div>
                  ${s.quote ? `
                    <div style="margin-top: 10px; font-style: italic; font-size: 0.85rem; color: var(--color-text-dark); border-left: 3px solid var(--color-primary-teal); padding-left: 12px;">
                      "${escapeHtml(s.quote)}"
                    </div>
                  ` : ''}
                  <div class="text-xs text-muted" style="margin-top: 8px;">
                    Source: ${escapeHtml(s.source || 'FDA')} | Chunk: <code>${escapeHtml(s.chunk_id || '')}</code>
                  </div>
                </div>
              `).join('')}
            </div>
          `}
        </div>
      </div>

      <div class="flex-between" style="margin-top: 24px;">
        <button class="btn btn-secondary btn-sm" type="button" id="btnP2ScanAnotherSuccess">Scan another side</button>
        ${cand.reference_label_url ? `
          <a class="btn btn-primary btn-sm" href="${escapeHtml(cand.reference_label_url)}" target="_blank" rel="noopener noreferrer">
            View reference source &rarr;
          </a>
        ` : ''}
      </div>
    `;

    // Tab switching interaction
    const tabGroup = container.querySelector('#p2TabGroup');
    const summaryContent = container.querySelector('#p2TabSummaryContent');
    const sourcesContent = container.querySelector('#p2TabSourcesContent');

    if (tabGroup) {
      tabGroup.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          tabGroup.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const tab = btn.dataset.tab;
          if (tab === 'summary') {
            if (summaryContent) summaryContent.style.display = 'block';
            if (sourcesContent) sourcesContent.style.display = 'none';
          } else if (tab === 'sources') {
            if (summaryContent) summaryContent.style.display = 'none';
            if (sourcesContent) sourcesContent.style.display = 'block';
          }
        });
      });
    }

    // Navigation buttons
    const askTeaser = container.querySelector('#btnP2AskTeaser');
    if (askTeaser) {
      askTeaser.addEventListener('click', () => {
        if (window.LabelLensStateSwitcher) {
          window.LabelLensStateSwitcher.setScreen('P3 Ask about this label', 'success');
        } else {
          window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
            detail: { screen: 'P3 Ask about this label' }
          }));
        }
      });
    }

    const scanAnother = container.querySelector('#btnP2ScanAnotherSuccess');
    if (scanAnother) {
      scanAnother.addEventListener('click', () => {
        if (window.LabelLensStateSwitcher) {
          window.LabelLensStateSwitcher.setScreen('P1 Scan and Understand', 'empty (idle)');
        } else {
          window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
            detail: { screen: 'P1 Scan and Understand' }
          }));
        }
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
