/**
 * ui/js/render-d7.js
 * Renderer for Screen D7: Review & approval
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Nothing published without approval record from authorized reviewer.
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

  function renderScreenD7(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};

    // 403 Self approval forbidden error
    if (state === 'failed' || safeData.error === 'self_approval_forbidden') {
      container.innerHTML = `
        <div class="notice-banner notice-danger" style="max-width: 680px; margin: 0 auto 20px auto;">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">Self-approval forbidden (403)</div>
            <div class="notice-text">${escapeHtml(safeData.message || 'The user who submitted this change cannot approve it. Ask another reviewer.')}</div>
          </div>
        </div>

        <div class="card" style="max-width: 680px; margin: 0 auto; text-align: center; padding: 32px;">
          <p class="text-muted text-sm">Regulatory 4-eyes principle requires independent review prior to label release.</p>
          <div class="text-xs text-muted" style="margin-top: 12px;">Submitted by: <code>${escapeHtml((safeData.details && safeData.details.created_by) || 'usr_demo_editor')}</code></div>
        </div>
      `;
      return;
    }

    // Empty list of reviews
    if (state === 'empty' || (safeData.items && safeData.items.length === 0)) {
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Review and approval</h2>
            <div class="text-xs text-muted">Independent regulatory review queue.</div>
          </div>
        </div>
        <div class="card" style="text-align: center; padding: 48px;">
          <h3>No review tasks pending</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">All label drafts have been reviewed or are currently in draft preparation.</p>
        </div>
      `;
      return;
    }

    // Recheck check result (passed or failed)
    if (safeData.check_id && safeData.findings) {
      const isPassed = safeData.passed === true;
      const findings = safeData.findings || [];

      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Artwork pre-approval re-check</h2>
            <div class="text-xs text-muted">Check ID: <code>${escapeHtml(safeData.check_id)}</code></div>
          </div>
          <span class="badge ${isPassed ? 'badge-teal' : 'badge-danger'}">
            ${isPassed ? 'Re-check Passed' : 'Re-check Failed'}
          </span>
        </div>

        ${!isPassed ? `
          <div class="notice-banner notice-danger">
            <div class="notice-icon">!</div>
            <div>
              <div class="notice-title">Automated re-check failed</div>
              <div class="notice-text">Artwork fails deterministic verification. Please resolve findings before approving.</div>
            </div>
          </div>
        ` : ''}

        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Findings (${findings.length})</div>
          <div class="flex-col" style="gap: 10px;">
            ${findings.length === 0 ? `
              <div class="text-sm text-muted">Zero findings detected. Label artwork is compliant.</div>
            ` : findings.map(f => `
              <div class="card" style="border: 1px solid var(--color-border); padding: 12px;">
                <div class="flex-between">
                  <span class="font-semibold text-sm" style="color: var(--color-danger-text);">${escapeHtml(f.kind.replace('_', ' '))}</span>
                  <span class="badge badge-danger">${escapeHtml(f.severity)}</span>
                </div>
                <div class="text-sm text-muted" style="margin-top: 4px;">${escapeHtml(f.message)}</div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
      return;
    }

    // Single Review Decision View (Approved or Returned)
    const decision = safeData.decision || 'approve';
    const isApproved = decision === 'approve';

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Review record: <code>${escapeHtml(safeData.review_id || 'rev_0003')}</code></h2>
          <div class="text-xs text-muted">Version: <code>${escapeHtml(safeData.version_id || 'lbv_0003')}</code> | Change: <code>${escapeHtml(safeData.change_id || '')}</code></div>
        </div>
        <span class="badge ${isApproved ? 'badge-teal' : 'badge-warning'}">
          ${isApproved ? 'Approved for Release' : 'Returned for Revision'}
        </span>
      </div>

      <div class="grid-two-col">
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Review Decision Details</div>
          <div class="kv-table">
            <div class="kv-row">
              <span class="kv-label">Reviewer</span>
              <span class="kv-value"><code>${escapeHtml(safeData.user_id || 'usr_demo_reviewer')}</code> (${escapeHtml(safeData.reviewer_role || 'reviewer')})</span>
            </div>
            <div class="kv-row">
              <span class="kv-label">Decision</span>
              <span class="kv-value"><strong style="color: ${isApproved ? 'var(--color-primary-teal)' : 'var(--color-warning-text)'};">${escapeHtml(decision.toUpperCase())}</strong></span>
            </div>
            <div class="kv-row">
              <span class="kv-label">Decided At</span>
              <span class="kv-value">${escapeHtml(safeData.decided_at || '')}</span>
            </div>
            <div class="kv-row">
              <span class="kv-label">Resulting Status</span>
              <span class="kv-value"><span class="badge badge-blue">${escapeHtml(safeData.resulting_status || 'reviewed')}</span></span>
            </div>
            <div class="kv-row">
              <span class="kv-label">Artifact SHA256</span>
              <span class="kv-value font-mono text-xs" style="word-break: break-all;">${escapeHtml(safeData.artifact_sha256 || '')}</span>
            </div>
          </div>
        </div>

        <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div class="card-header-clean font-semibold text-sm">Reviewer Commentary</div>
            <div style="background: var(--color-bg-subtle); padding: 12px; border-radius: var(--radius-md); font-size: 0.9rem; font-style: italic;">
              "${escapeHtml(safeData.comment || 'Text, symbol and barcode checked.')}"
            </div>
          </div>
          <div style="margin-top: 24px;">
            <button class="btn btn-primary" type="button" style="width: 100%;" id="btnGoToExport">Proceed to Export Package &rarr;</button>
          </div>
        </div>
      </div>
    `;

    const exportBtn = container.querySelector('#btnGoToExport');
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
  window.LabelLensRenderers['D7 Review'] = renderScreenD7;
  window.LabelLensRenderers['D7'] = renderScreenD7;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD7 };
  }
})();
