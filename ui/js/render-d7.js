/**
 * ui/js/render-d7.js
 * Renderer for Screen D7: Review & approval
 *
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Nothing published without approval record from authorized reviewer.
 * - Never invent data: blocked reasons come only from the mock state in front of us.
 * - No em dashes.
 */

(function() {
  const esc = (s) => window.LabelLensData.escapeHtml(s);

  function prettyKind(kind) {
    return String(kind || 'finding').split('_').join(' ');
  }

  function shortHash(h) {
    return h ? `<code title="${esc(h)}">${esc(String(h).slice(0, 16))}...</code>` : '<span class="text-muted">none</span>';
  }

  /** Decision form. `blocked` is a list of reasons; empty list means the buttons are live. */
  function decisionPanel(blocked, ctx) {
    const isBlocked = blocked.length > 0;
    return `
      <div class="card" style="margin-top: 16px;" data-testid="decision-panel">
        <div class="card-header-clean font-semibold text-sm">Reviewer decision</div>
        ${isBlocked ? `
          <div class="notice-banner notice-danger" data-testid="approval-blocked" style="margin-bottom: 12px;">
            <div class="notice-icon">!</div>
            <div>
              <div class="notice-title">Approval blocked</div>
              <ul class="notice-text" style="margin: 4px 0 0 16px;">
                ${blocked.map(r => `<li>${esc(r)}</li>`).join('')}
              </ul>
            </div>
          </div>` : `
          <div class="text-xs text-muted" style="margin-bottom: 8px;">
            Approval is bound to the artifact hash ${shortHash(ctx.hash)} and check <code>${esc(ctx.check_id || '')}</code>.
            A newer version voids it. The author of the change cannot approve it.
          </div>`}
        <textarea id="reviewComment" rows="2" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: var(--radius-md);" placeholder="Reviewer comment (required to return)"></textarea>
        <div class="flex-row" style="gap: 8px; margin-top: 10px;">
          <button class="btn btn-primary" type="button" id="btnApprove" ${isBlocked ? 'disabled aria-disabled="true"' : ''}>Approve</button>
          <button class="btn btn-secondary" type="button" id="btnReturn">Return for revision</button>
        </div>
        <div class="text-xs text-muted" id="reviewActionNote" style="margin-top: 8px;"></div>
      </div>`;
  }

  function bindDecision(container, ctx) {
    const note = container.querySelector('#reviewActionNote');
    const send = async (decision) => {
      const comment = (container.querySelector('#reviewComment') || {}).value || '';
      if (decision === 'return' && !comment.trim()) {
        note.textContent = 'A comment is required to return a version.';
        return;
      }
      const actions = window.LabelLensActions;
      if (actions && actions.reviewArtwork && window.LabelLensData.CONFIG.mode === 'api') {
        note.textContent = 'Sending...';
        try {
          const res = await actions.reviewArtwork(ctx, decision, comment);
          note.textContent = res.message;
        } catch (e) {
          note.textContent = 'Request failed: ' + e.message;
        }
      } else {
        note.textContent = 'Mock mode: no request sent. Nothing was approved or returned.';
      }
    };
    const a = container.querySelector('#btnApprove');
    const r = container.querySelector('#btnReturn');
    if (a) a.addEventListener('click', () => { if (!a.disabled) send('approve'); });
    if (r) r.addEventListener('click', () => send('return'));
  }

  function coverageTable(coverage) {
    if (!coverage || !coverage.length) return '';
    const rows = coverage.map(c => {
      const cls = c.outcome === 'pass' ? 'badge-teal' : (c.outcome === 'needs_human' ? 'badge-warning' : (c.outcome === 'fail' ? 'badge-danger' : 'badge-blue'));
      return `<tr>
        <td class="font-mono text-xs">${esc(c.rule_id)}</td>
        <td><span class="badge ${cls}">${esc(c.outcome)}</span></td>
        <td class="text-xs text-muted">${esc(c.reason || '')}</td></tr>`;
    }).join('');
    return `
      <div class="card" style="margin-top: 16px;" data-testid="coverage">
        <div class="card-header-clean font-semibold text-sm">Rule coverage (${coverage.length} rules)</div>
        <table style="width: 100%; border-collapse: collapse;">
          <thead><tr class="text-xs text-muted" style="text-align: left;"><th>Rule</th><th>Outcome</th><th>Reason</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function renderRecheck(container, d) {
    const isPassed = d.passed === true;
    const findings = d.findings || [];
    const needsHuman = d.needs_human_count || (d.coverage || []).filter(c => c.outcome === 'needs_human').length;
    const nCrit = d.critical_count || findings.length;
    const blocked = [];
    if (!isPassed) {
      blocked.push(`Re-check ${d.check_id} did not pass (${nCrit} critical finding${nCrit === 1 ? '' : 's'}). Fix the artwork and generate a new version.`);
    }
    container.innerHTML = `
      ${window.LabelLensData.renderDraftBanner('This version stays a draft until a reviewer other than its author approves it.')}
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Artwork pre-approval re-check</h2>
          <div class="text-xs text-muted">Check ID: <code>${esc(d.check_id)}</code> | Version: <code>${esc(d.version_id || '')}</code> | Artifact ${shortHash(d.artifact_sha256)}</div>
        </div>
        <span class="badge ${isPassed ? 'badge-teal' : 'badge-danger'}">${isPassed ? 'Re-check passed' : 'Re-check failed'}</span>
      </div>

      ${!isPassed ? `
        <div class="notice-banner notice-danger">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">Automated re-check failed</div>
            <div class="notice-text">Resolve the findings before approving.</div>
          </div>
        </div>` : ''}

      ${isPassed && needsHuman > 0 ? `
        <div class="notice-banner notice-warning" data-testid="needs-human">
          <div class="notice-icon">i</div>
          <div>
            <div class="notice-title">${needsHuman} rule${needsHuman === 1 ? '' : 's'} need a human decision</div>
            <div class="notice-text">A passed re-check is not a compliance determination. The reviewer must look at the items marked needs_human below.</div>
          </div>
        </div>` : ''}

      <div class="card">
        <div class="card-header-clean font-semibold text-sm">Findings (${findings.length})</div>
        <div class="flex-col" style="gap: 10px;">
          ${findings.length === 0 ? '<div class="text-sm text-muted">No problem findings in this check.</div>' : findings.map(f => `
            <div class="card" style="border: 1px solid var(--color-border); padding: 12px;">
              <div class="flex-between">
                <span class="font-semibold text-sm" style="color: var(--color-danger-text);">${esc(prettyKind(f.kind))}${f.field ? ' (' + esc(f.field) + ')' : ''}</span>
                <span class="badge badge-danger">${esc(f.severity)}</span>
              </div>
              <div class="text-sm text-muted" style="margin-top: 4px;">${esc(f.message)}</div>
              ${f.observed || f.expected ? `<div class="text-xs" style="margin-top: 4px;">Observed: <code>${esc(f.observed)}</code> | Expected: <code>${esc(f.expected)}</code></div>` : ''}
            </div>`).join('')}
        </div>
      </div>
      ${coverageTable(d.coverage)}
      ${decisionPanel(blocked, { hash: d.artifact_sha256, check_id: d.check_id })}
    `;
    bindDecision(container, { check_id: d.check_id, version_id: d.version_id, label_id: d.label_id, artifact_sha256: d.artifact_sha256 });
  }

  function renderBodyD7(container, state, meta, data) {
    if (!container) return;
    const d = data || {};

    // 403 self approval
    if (d.error === 'self_approval_forbidden') {
      container.innerHTML = `
        ${window.LabelLensData.renderDraftBanner()}
        <div class="notice-banner notice-danger" data-testid="approval-blocked" style="max-width: 680px; margin: 0 auto 20px auto;">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">Approval blocked: self-approval forbidden (403)</div>
            <div class="notice-text">${esc(d.message)}</div>
          </div>
        </div>
        <div class="card" style="max-width: 680px; margin: 0 auto; text-align: center; padding: 32px;">
          <p class="text-muted text-sm">Independent review is required before a label is released.</p>
          <div class="text-xs text-muted" style="margin-top: 12px;">Change <code>${esc((d.details || {}).change_id || '')}</code> was submitted by <code>${esc((d.details || {}).created_by || '')}</code>.</div>
        </div>`;
      return;
    }

    // Empty list of reviews
    if (d.items && d.items.length === 0) {
      container.innerHTML = `
        ${window.LabelLensData.renderDraftBanner()}
        <div style="margin-bottom: 16px;">
          <h2>Review and approval</h2>
          <div class="text-xs text-muted">Version: <code>${esc(d.version_id || '')}</code></div>
        </div>
        <div class="card" style="text-align: center; padding: 48px;">
          <h3>No review on record for this version</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">No one has approved or returned it, so it is still a draft.</p>
        </div>`;
      return;
    }

    // Re-check result
    if (d.check_id && d.findings) {
      renderRecheck(container, d);
      return;
    }

    // Single review record (approved or returned)
    const isApproved = d.decision === 'approve';
    container.innerHTML = `
      ${isApproved
        ? `<div class="notice-banner notice-warning" data-testid="draft-banner"><div class="notice-icon">i</div><div>
             <div class="notice-title"><span class="badge badge-draft">DRAFT</span> Approval record on file</div>
             <div class="notice-text">${esc(window.LabelLensData.DRAFT_DISCLAIMER)} The approval is bound to the artifact hash below and is voided by any newer version.</div></div></div>`
        : window.LabelLensData.renderDraftBanner('Returned for revision: the version is back in draft.')}
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Review record: <code>${esc(d.review_id || '')}</code></h2>
          <div class="text-xs text-muted">Version: <code>${esc(d.version_id || '')}</code> | Change: <code>${esc(d.change_id || '')}</code> | Check: <code>${esc(d.check_id || 'none')}</code></div>
        </div>
        <span class="badge ${isApproved ? 'badge-teal' : 'badge-warning'}">${isApproved ? 'Approved' : 'Returned for revision'}</span>
      </div>

      <div class="grid-two-col">
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Decision details</div>
          <div class="kv-table">
            <div class="kv-row"><span class="kv-label">Reviewer</span><span class="kv-value"><code>${esc(d.user_id)}</code> (${esc(d.reviewer_role)})</span></div>
            <div class="kv-row"><span class="kv-label">Decision</span><span class="kv-value"><strong>${esc(String(d.decision || '').toUpperCase())}</strong></span></div>
            <div class="kv-row"><span class="kv-label">Decided at</span><span class="kv-value">${esc(d.decided_at)}</span></div>
            <div class="kv-row"><span class="kv-label">Resulting status</span><span class="kv-value"><span class="badge badge-blue">${esc(d.resulting_status)}</span></span></div>
            <div class="kv-row"><span class="kv-label">Artifact SHA256</span><span class="kv-value font-mono text-xs" style="word-break: break-all;">${esc(d.artifact_sha256)}</span></div>
          </div>
        </div>
        <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div class="card-header-clean font-semibold text-sm">Reviewer comment</div>
            <div style="background: var(--color-bg-subtle); padding: 12px; border-radius: var(--radius-md); font-size: 0.9rem; font-style: italic;">"${esc(d.comment)}"</div>
          </div>
          <div style="margin-top: 24px;">
            <button class="btn btn-primary" type="button" style="width: 100%;" id="btnGoToExport">Go to export package &rarr;</button>
          </div>
        </div>
      </div>`;

    const exportBtn = container.querySelector('#btnGoToExport');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        window.dispatchEvent(new CustomEvent('labellens:screen-navigated', { detail: { screen: 'D8 Export' } }));
      });
    }
  }

  /** In api mode a card on top runs the real re-check on the live version (the one just generated, or ?version=). */
  function renderScreenD7(container, state, meta, data) {
    if (!container) return;
    if (window.LabelLensData.CONFIG.mode !== 'api') { renderBodyD7(container, state, meta, data); return; }
    const vid = (window.LabelLensData.CONFIG.ids || {}).version_id;
    const user = window.LabelLensData.CONFIG.currentUserHeader;
    container.innerHTML = `
      <div class="card" style="margin-bottom: 16px;" data-testid="recheck-card">
        <div class="card-header-clean font-semibold text-sm">Re-check a generated version (live)</div>
        <div class="text-xs text-muted">Version: ${vid ? '<code>' + esc(vid) + '</code>' : 'none yet. Generate a draft in Changes first, or open the page with ?version=...'} | Acting as <code id="d7Acting">${esc(user)}</code> (switch in the header)</div>
        <div class="flex-row" style="gap: 8px; margin-top: 8px;">
          <button class="btn btn-primary btn-sm" type="button" id="btnLiveRecheck" ${vid ? '' : 'disabled aria-disabled="true"'}>Run re-check</button>
        </div>
        <div class="text-xs text-muted" id="d7LiveNote" style="margin-top: 6px;"></div>
      </div>
      <div id="d7Body"></div>`;
    const body = container.querySelector('#d7Body');
    renderBodyD7(body, state, meta, data);
    const note = container.querySelector('#d7LiveNote');
    container.querySelector('#btnLiveRecheck').addEventListener('click', async () => {
      note.textContent = 'Reading the rendered PDF back and running the checker...';
      try {
        const res = await window.LabelLensActions.recheck(vid, (j) => { note.textContent = `${j.state}${j.message ? ': ' + j.message : ''}`; });
        window.LabelLensData.setDataSource('api', 'recheckArtwork');
        renderBodyD7(body, 'success', null, res);
        note.textContent = `Check ${res.check_id}: ${res.passed ? 'passed' : 'did not pass'}.`;
      } catch (e) { note.textContent = 'Re-check failed: ' + e.message; }
    });
  }

  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D7 Review'] = renderScreenD7;
  window.LabelLensRenderers['D7'] = renderScreenD7;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD7 };
  }
})();
