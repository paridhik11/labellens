/**
 * ui/js/render-d6.js
 * Renderer for Screen D6: Changes ("Change impact", Mockup Panel 4)
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Mark all drafts clearly: DRAFT watermark and required disclaimer.
 * - Deterministic templates only.
 * - Never invent GTIN or UDI-DI.
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

  function renderScreenD6(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    // Loading State
    if (state === 'loading' || (safeData.state && safeData.state === 'processing')) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px; max-width: 600px; margin: 0 auto;">
          <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Job ID: <code>${escapeHtml(safeData.job_id || 'job_gen_0001')}</code></div>
          <h3>Generating deterministic artwork draft...</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">Applying template slots and inserting mandatory DRAFT watermark.</p>
          <div style="width: 280px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 24px auto; overflow: hidden;">
            <div style="width: 60%; height: 100%; background: var(--color-draft-purple);"></div>
          </div>
        </div>
      `;
      return;
    }

    // Identifier Required / Needs Input State (409)
    if (state && state.includes('needs_input')) {
      container.innerHTML = `
        <div class="notice-banner notice-warning" style="max-width: 700px; margin: 0 auto 20px auto;">
          <div class="notice-icon">i</div>
          <div>
            <div class="notice-title">Identifier required</div>
            <div class="notice-text">${escapeHtml(safeData.message || 'A valid UDI-DI or GTIN is required before artwork generation can proceed.')}</div>
          </div>
        </div>

        <div class="card" style="max-width: 700px; margin: 0 auto; padding: 24px;">
          <h3>Missing Required Identifier</h3>
          <p class="text-muted text-sm" style="margin-top: 6px;">Per system policy, GTIN and UDI-DI values are never invented. Please provide a verified GS1 identifier.</p>
          <div style="margin-top: 16px;">
            <label class="text-xs font-semibold text-muted" style="display: block; margin-bottom: 6px;">Provide Primary UDI-DI:</label>
            <input type="text" placeholder="(01)00000000000000 [TEST]" style="width: 100%; padding: 8px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); font-family: monospace;">
            <button class="btn btn-primary" type="button" style="margin-top: 12px;">Submit Identifier &amp; Resume</button>
          </div>
        </div>
      `;
      return;
    }

    // Standard Change Assessment / Impact View (Mockup Panel 4)
    const change = safeData.change || safeData;
    const affected = safeData.affected || [];

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Change impact</h2>
          <div class="text-xs text-muted" style="margin-top: 2px;">Automated assessment of proposed label modifications across packaging hierarchy.</div>
        </div>
        <span class="badge badge-blue">Change ID: ${escapeHtml(change.change_id || 'chg_0002')}</span>
      </div>

      <!-- Proposed Change Hero Card -->
      <div class="card" style="margin-bottom: 20px; background-color: #f8fafc;">
        <div class="flex-row" style="gap: 12px;">
          <div style="background-color: var(--color-info-blue-bg); color: var(--color-info-blue-text); padding: 8px; border-radius: var(--radius-md); font-size: 1.25rem;">📄</div>
          <div>
            <div class="font-semibold text-sm">Proposed change: sterilization method</div>
            <div class="text-sm text-muted" style="margin-top: 2px;">${escapeHtml(change.raw_text || 'Update the sterilization method from ethylene oxide (EO) to gamma irradiation.')}</div>
          </div>
        </div>
      </div>

      <div class="grid-two-col">
        <!-- Left: Affected Items Checklist -->
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Affected items (${affected.length})</div>
          <div class="flex-col" style="gap: 10px;">
            ${affected.map(item => `
              <div class="card" style="border: 1px solid var(--color-border); padding: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <div class="font-semibold text-sm">${escapeHtml(item.title)}</div>
                  <div class="text-xs text-muted">${escapeHtml(item.description)}</div>
                </div>
                <div>
                  <span class="badge ${item.suggestion === 'edit_required' ? 'badge-danger' : (item.suggestion === 'no_change' ? 'badge-teal' : 'badge-warning')}">
                    ${escapeHtml(item.suggestion.replace('_', ' '))} &gt;
                  </span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Right: Side-by-side Revision Preview with DRAFT watermark -->
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Label revision preview</div>
          
          <div class="grid-two-col" style="gap: 12px;">
            <!-- Current L2 -->
            <div style="border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px;">
              <div class="flex-between" style="margin-bottom: 8px;">
                <span class="badge badge-blue">Current L2</span>
              </div>
              <div class="text-xs font-semibold">ExampleDevice™</div>
              <div class="text-xs text-muted" style="margin: 4px 0;">Sterilized using ethylene oxide (EO).</div>
              <div style="border: 1px solid #334155; padding: 2px 4px; display: inline-block; font-size: 0.7rem; font-weight: 700; margin-top: 8px;">STERILE EO</div>
            </div>

            <!-- Draft L3 with DRAFT mark -->
            <div style="border: 2px dashed var(--color-draft-purple); border-radius: var(--radius-md); padding: 12px; background-color: var(--color-draft-purple-bg); position: relative;">
              <div class="flex-between" style="margin-bottom: 8px;">
                <span class="badge badge-purple">Draft L3</span>
                <span class="badge badge-draft">DRAFT</span>
              </div>
              <div class="text-xs font-semibold">ExampleDevice™</div>
              <div class="text-xs text-muted" style="margin: 4px 0;">Sterilized using gamma irradiation.</div>
              <div style="border: 1px solid #334155; padding: 2px 4px; display: inline-block; font-size: 0.7rem; font-weight: 700; margin-top: 8px;">STERILE R</div>
              
              <div class="text-xs" style="color: var(--color-draft-purple); font-size: 0.68rem; margin-top: 10px; font-weight: 600;">
                Draft generated for review. Not a compliance determination.
              </div>
            </div>
          </div>

          <!-- Change Timeline -->
          <div style="margin-top: 24px;">
            <div class="text-xs font-semibold text-muted">Change timeline</div>
            <div class="timeline-stepper">
              <div class="timeline-step active">
                <div class="timeline-dot"></div>
                <span>Draft</span>
              </div>
              <div class="timeline-line"></div>
              <div class="timeline-step">
                <div class="timeline-dot"></div>
                <span>Checked</span>
              </div>
              <div class="timeline-line"></div>
              <div class="timeline-step">
                <div class="timeline-dot"></div>
                <span>Reviewed</span>
              </div>
              <div class="timeline-line"></div>
              <div class="timeline-step">
                <div class="timeline-dot"></div>
                <span>Published</span>
              </div>
            </div>
          </div>

          <div class="flex-between" style="margin-top: 20px;">
            <button class="btn btn-secondary btn-sm" type="button" id="btnGoToEvidence">View evidence</button>
            <div>
              <button class="btn btn-primary btn-sm" type="button" id="btnGoToReview">Create review task</button>
              <div class="text-xs text-muted" style="margin-top: 2px; text-align: right;">Human approval before publication.</div>
            </div>
          </div>
        </div>
      </div>
    `;

    const evidenceBtn = container.querySelector('#btnGoToEvidence');
    if (evidenceBtn) {
      evidenceBtn.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
          detail: { screen: 'D5 Evidence' }
        }));
      });
    }

    const reviewBtn = container.querySelector('#btnGoToReview');
    if (reviewBtn) {
      reviewBtn.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('labellens:screen-navigated', {
          detail: { screen: 'D7 Review' }
        }));
      });
    }
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D6 Changes'] = renderScreenD6;
  window.LabelLensRenderers['D6'] = renderScreenD6;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD6 };
  }
})();
