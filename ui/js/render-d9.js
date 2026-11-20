/**
 * ui/js/render-d9.js
 * Renderer for Screen D9: History (Audit Log and Versions)
 * 
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Fixed audit trail: immutable events (21 CFR 11 & 21 CFR 820.181 DMR).
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

  function getActionBadgeClass(action) {
    const act = String(action || '').toLowerCase();
    if (act.includes('approved') || act.includes('passed')) return 'badge-teal';
    if (act.includes('published')) return 'badge-blue';
    if (act.includes('returned')) return 'badge-warning';
    if (act.includes('rejected') || act.includes('failed')) return 'badge-danger';
    if (act.includes('generated')) return 'badge-purple';
    return 'badge-blue';
  }

  function renderScreenD9(container, state, meta, data) {
    if (!container) return;
    const safeData = data || {};
    const stateStr = String(state || '').toLowerCase();
    const items = safeData.items || [];
    const versions = safeData.versions || [];

    // 1. Empty State
    if (stateStr === 'empty' || (items.length === 0 && versions.length === 0)) {
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Product History &amp; Audit Trail</h2>
            <div class="text-xs text-muted">Product ID: <code>${escapeHtml(safeData.product_id || 'prd_samplecatheter')}</code></div>
          </div>
          <span class="badge badge-draft">0 Events</span>
        </div>

        <div class="card" style="text-align: center; padding: 48px; max-width: 650px; margin: 20px auto;">
          <div style="font-size: 2.5rem; margin-bottom: 12px;">📋</div>
          <h3>No Audit Events Recorded</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">
            No lifecycle events or regulatory audits exist for product <code>${escapeHtml(safeData.product_id || 'prd_samplecatheter')}</code> yet.
          </p>
          <div class="text-xs text-muted" style="margin-top: 16px;">
            Audit records will be created automatically upon template registration, scan inspection, or change creation.
          </div>
        </div>
      `;
      return;
    }

    // 2. Label Versions History View (LabelVersionList schema)
    if (versions.length > 0 || stateStr.includes('label versions') || safeData.label_id) {
      container.innerHTML = `
        <div class="flex-between" style="margin-bottom: 16px;">
          <div>
            <h2>Label Versions Lineage</h2>
            <div class="text-xs text-muted">
              Label ID: <code>${escapeHtml(safeData.label_id || 'lbl_exampledevice_carton')}</code>
              ${safeData.product_id ? ` : Product: <code>${escapeHtml(safeData.product_id)}</code>` : ''}
            </div>
          </div>
          <div class="flex-row" style="gap: 8px;">
            <button class="btn btn-secondary btn-sm" type="button" id="btnSwitchToAuditLog">View Audit Log</button>
            <span class="badge badge-teal">${versions.length} Version(s)</span>
          </div>
        </div>

        <div class="card">
          <div class="card-header-clean flex-between">
            <span class="font-semibold text-sm">Version Lineage &amp; Artifact History</span>
            <span class="text-xs text-muted">Ordered chronological revisions</span>
          </div>

          <div class="flex-col" style="gap: 12px; margin-top: 10px;">
            ${versions.map(v => `
              <div class="card" style="border: 1px solid var(--color-border); padding: 14px;">
                <div class="flex-between">
                  <div class="flex-row" style="gap: 8px;">
                    <span class="font-semibold text-sm font-mono">${escapeHtml(v.version_id)}</span>
                    <span class="badge badge-purple text-xs">v${v.artwork_version || 1}</span>
                    <span class="badge ${v.kind === 'generated' ? 'badge-blue' : 'badge-teal'} text-xs">${escapeHtml(v.kind || 'uploaded')}</span>
                  </div>
                  <span class="badge ${v.status === 'published' ? 'badge-teal' : (v.status === 'draft' ? 'badge-draft' : 'badge-blue')}">
                    ${escapeHtml(v.status || 'published')}
                  </span>
                </div>

                <div class="grid-two-col" style="gap: 12px; margin-top: 10px; font-size: 0.75rem;">
                  <div>
                    <div class="text-muted">Template: <code>${escapeHtml(v.template_id || 'tpl_exampledevice_carton')}</code> (v${v.template_version || 1})</div>
                    <div class="text-muted" style="margin-top: 2px;">
                      Created: ${escapeHtml(v.created_at || '')} by <code>${escapeHtml(v.created_by || 'usr_demo_editor')}</code>
                    </div>
                    ${v.parent_version_id ? `
                      <div class="text-muted" style="margin-top: 2px;">
                        Derived from: <code>${escapeHtml(v.parent_version_id)}</code>
                      </div>
                    ` : ''}
                  </div>

                  <div>
                    ${v.latest_review_id ? `
                      <div class="text-muted">Review ID: <code>${escapeHtml(v.latest_review_id)}</code></div>
                    ` : ''}
                    <div class="flex-row" style="gap: 8px; margin-top: 6px;">
                      ${v.artwork_file ? `
                        <a href="${escapeHtml(v.artwork_file)}" class="btn btn-secondary btn-sm" style="font-size: 0.7rem; padding: 2px 8px;" download>SVG Artwork</a>
                      ` : ''}
                      ${v.pdf_file ? `
                        <a href="${escapeHtml(v.pdf_file)}" class="btn btn-secondary btn-sm" style="font-size: 0.7rem; padding: 2px 8px;" download>PDF Package</a>
                      ` : ''}
                    </div>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;

      const auditBtn = container.querySelector('#btnSwitchToAuditLog');
      if (auditBtn) {
        auditBtn.addEventListener('click', () => {
          window.LabelLensStateSwitcher.setScreen('D9 History', 'success (audit)');
        });
      }
      return;
    }

    // 3. Immutable Audit Events Trail (AuditEventList schema)
    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Audit Trail : ${escapeHtml(safeData.product_id || 'prd_exampledevice')}</h2>
          <div class="text-xs text-muted">21 CFR 820.181 Device Master Record &amp; 21 CFR Part 11 Immutable Electronic Records</div>
        </div>
        <div class="flex-row" style="gap: 8px;">
          <button class="btn btn-secondary btn-sm" type="button" id="btnSwitchToVersions">View Label Versions</button>
          <span class="badge badge-teal">${items.length} Recorded Event(s)</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header-clean flex-between">
          <span class="font-semibold text-sm">Regulatory Event Log</span>
          <span class="text-xs text-muted">Append-only audit trail</span>
        </div>

        <div class="flex-col" style="gap: 12px; margin-top: 10px;">
          ${items.map(evt => `
            <div class="card" style="border: 1px solid var(--color-border); padding: 12px;">
              <div class="flex-between">
                <div class="flex-row" style="gap: 8px;">
                  <span class="badge ${getActionBadgeClass(evt.action)}">${escapeHtml(evt.action || 'event')}</span>
                  <span class="font-mono text-xs text-muted">ID: ${escapeHtml(evt.event_id)}</span>
                </div>
                <span class="text-xs text-muted font-mono">${escapeHtml(evt.at || '')}</span>
              </div>

              <div class="flex-between" style="margin-top: 8px; font-size: 0.75rem;">
                <div>
                  <span class="text-muted">Actor:</span> <code>${escapeHtml(evt.user_id || 'system')}</code>
                  <span class="text-muted" style="margin-left: 8px;">Target:</span>
                  <code>${escapeHtml(evt.entity_type || '')}</code> (${escapeHtml(evt.entity_id || '')})
                </div>
                ${evt.version_before !== undefined && evt.version_after !== undefined ? `
                  <div class="badge badge-purple text-xs">
                    Version Transition: v${evt.version_before} &rarr; v${evt.version_after}
                  </div>
                ` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    const versionsBtn = container.querySelector('#btnSwitchToVersions');
    if (versionsBtn) {
      versionsBtn.addEventListener('click', () => {
        window.LabelLensStateSwitcher.setScreen('D9 History', 'success (label versions)');
      });
    }
  }

  // Register renderer
  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D9 History'] = renderScreenD9;
  window.LabelLensRenderers['D9'] = renderScreenD9;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD9 };
  }
})();
