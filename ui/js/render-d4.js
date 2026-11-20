/**
 * ui/js/render-d4.js
 * Renderer for Screen D4: Inspect (extraction, confirmation, inspection result)
 *
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Every value on screen comes from the payload (mock or live). No hard-coded product, date or barcode text.
 * - Low-confidence (unclear) fields are editable until the extraction is confirmed.
 * - DRAFT disclaimer on the screen. A passed check is not a compliance determination.
 * - No em dashes.
 */

(function() {
  const esc = (s) => window.LabelLensData.escapeHtml(s);
  const testBadge = (v) => window.LabelLensData.renderTestBadge(v);
  const isApi = () => window.LabelLensData.CONFIG.mode === 'api';
  const kindText = (k) => String(k || 'finding').split('_').join(' ');

  function banner(d) {
    return window.LabelLensData.renderDraftBanner(d && d.disclaimer && d.disclaimer !== window.LabelLensData.DRAFT_DISCLAIMER ? d.disclaimer : '');
  }

  function goto(screen, state) {
    if (window.LabelLensStateSwitcher) window.LabelLensStateSwitcher.setScreen(screen, state || null);
  }

  function renderLoading(container, d) {
    const pct = Math.round((typeof d.progress === 'number' ? d.progress : 0.4) * 100);
    container.innerHTML = `
      ${banner(d)}
      <div class="card" data-testid="inspect-loading" style="text-align: center; padding: 48px 24px; max-width: 600px; margin: 0 auto;">
        <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Job <code>${esc(d.job_id)}</code> | ${esc(d.kind)} | ${esc(d.state)}</div>
        <h3>Running the checks...</h3>
        <p class="text-muted text-sm" style="margin-top: 8px;">${esc(d.message || '')}</p>
        <div style="width: 280px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 24px auto; overflow: hidden;">
          <div style="width: ${pct}%; height: 100%; background: var(--color-primary-blue);"></div>
        </div>
        <div class="text-xs text-muted">${pct}%</div>
        ${isApi() ? '' : '<div style="margin-top: 16px;"><button class="btn btn-sm btn-primary" type="button" id="btnSkipInspectLoading">View inspection results &rarr;</button></div>'}
      </div>`;
    const skip = container.querySelector('#btnSkipInspectLoading');
    if (skip) skip.addEventListener('click', () => goto('D4 Inspect', 'success'));
  }

  function barcodesHtml(barcodes) {
    if (!barcodes || !barcodes.length) return '<div class="text-xs text-muted">No barcode was decoded.</div>';
    return barcodes.map(b => `
      <div style="border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 8px 10px; background: var(--color-bg-subtle);" data-testid="barcode">
        <div class="font-semibold text-xs">${esc(b.type)}</div>
        <div class="font-mono text-xs" style="word-break: break-all;">${esc(b.raw)}</div>
        ${b.parsed ? `<div class="text-xs text-muted" style="margin-top: 4px;">${Object.entries(b.parsed).map(([k, v]) => `(${esc(k)}) ${esc(v)} ${testBadge(v)}`).join(' | ')}</div>` : ''}
      </div>`).join('');
  }

  function renderExtraction(container, d) {
    const fields = d.fields || {};
    const unclear = d.unclear_fields || [];
    const warnings = d.warnings || [];
    const confirmed = d.confirmed === true;
    const symbols = d.symbols || [];
    const blocks = d.ocr_blocks || [];
    const title = fields.product_name || fields.name || d.version_id || 'Label';
    container.innerHTML = `
      ${banner(d)}
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <div class="flex-row" style="gap: 8px;">
            <h2>Label extraction: ${esc(title)}</h2>
            <span class="badge ${confirmed ? 'badge-teal' : (unclear.length ? 'badge-warning' : 'badge-blue')}" data-testid="extraction-status">
              ${confirmed ? 'Extraction confirmed' : (unclear.length ? 'Review needed' : 'Extraction done, not confirmed')}
            </span>
          </div>
          <div class="text-xs text-muted" style="margin-top: 4px;">
            Label <code>${esc(d.label_id)}</code> | Version <code>${esc(d.version_id)}</code>${d.confirmed_by ? ` | Confirmed by <code>${esc(d.confirmed_by)}</code>` : ''}
          </div>
        </div>
        <div class="flex-row" style="gap: 8px;">
          ${confirmed ? '' : '<button class="btn btn-sm btn-primary" type="button" id="btnConfirmExtractionAction">Confirm extraction</button>'}
          <button class="btn btn-sm ${confirmed ? 'btn-primary' : 'btn-secondary'}" type="button" id="btnRunInspectionNow">Run inspection checks &rarr;</button>
        </div>
      </div>
      <div class="text-xs text-muted" id="d4Note" data-testid="d4-note" style="margin-bottom: 10px;"></div>

      ${!confirmed && unclear.length ? `
        <div class="notice-banner notice-warning" data-testid="unclear-banner">
          <div class="notice-icon">i</div>
          <div style="flex: 1;">
            <div class="notice-title">Confirm extracted fields (${unclear.length} unclear)</div>
            <div class="notice-text">Reading confidence was low for <strong>${unclear.map(esc).join(', ')}</strong>. Correct them below, then confirm.${warnings.length ? ' Warnings: ' + warnings.map(esc).join('; ') : ''}</div>
          </div>
        </div>` : (warnings.length ? `<div class="notice-banner notice-warning"><div class="notice-icon">i</div><div class="notice-text">Warnings: ${warnings.map(esc).join('; ')}</div></div>` : '')}

      <div class="grid-two-col">
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Extracted fields (${Object.keys(fields).length})</div>
          <div class="kv-table">
            ${Object.entries(fields).map(([k, v]) => {
              const edit = !confirmed && unclear.includes(k);
              return `
                <div class="kv-row" style="${edit ? 'background: rgba(245, 158, 11, 0.08); padding: 6px;' : ''}">
                  <span class="kv-label">${esc(k)}</span>
                  <span class="kv-value">${edit
                    ? `<input type="text" data-field="${esc(k)}" data-testid="edit-${esc(k)}" value="${esc(v)}" style="width: 100%; border: 1px solid #f59e0b; border-radius: 4px; padding: 4px 8px; font-size: 0.8rem;"><span class="badge badge-warning" style="margin-top: 4px;">Needs confirmation</span>`
                    : `${esc(v)} ${testBadge(v)}`}</span>
                </div>`;
            }).join('')}
          </div>
        </div>
        <div class="flex-col" style="gap: 16px;">
          <div class="card">
            <div class="card-header-clean font-semibold text-sm">Barcodes (${(d.barcodes || []).length})</div>
            <div class="flex-col" style="gap: 8px;">${barcodesHtml(d.barcodes)}</div>
          </div>
          <div class="card">
            <div class="card-header-clean flex-between"><span class="font-semibold text-sm">Detected symbols (${symbols.length})</span><span class="badge badge-purple">ISO 15223-1</span></div>
            <div class="flex-col" style="gap: 6px;">
              ${symbols.length ? symbols.map(sym => `
                <div class="flex-between" style="border: 1px solid var(--color-border); padding: 6px 10px; border-radius: 4px; background: var(--color-bg-subtle);">
                  <span class="font-semibold text-xs">${esc(sym.name)}</span>
                  <span class="text-xs text-muted">Confidence: ${Math.round((sym.conf || 0) * 100)}%</span>
                </div>`).join('') : '<div class="text-xs text-muted">No symbol detected.</div>'}
            </div>
          </div>
          <div class="card">
            <div class="card-header-clean font-semibold text-sm">Text read from the label (${blocks.length} blocks)</div>
            <div class="flex-col" style="gap: 4px; max-height: 220px; overflow: auto;">
              ${blocks.map(b => `<div class="flex-between text-xs"><span class="font-mono">${esc(b.text)}</span><span class="text-muted">${Math.round((b.conf || 0) * 100)}%</span></div>`).join('') || '<div class="text-xs text-muted">No text blocks.</div>'}
            </div>
          </div>
        </div>
      </div>`;

    const note = container.querySelector('#d4Note');
    const confirmBtn = container.querySelector('#btnConfirmExtractionAction');
    if (confirmBtn) confirmBtn.addEventListener('click', async () => {
      if (!isApi()) { goto('D4 Inspect', 'success (confirmed extraction)'); return; }
      const values = {};
      const inputs = container.querySelectorAll('input[data-field]');
      inputs.forEach(i => { values[i.dataset.field] = i.value; });
      // With nothing unclear the confirmation carries the values as read, so the record shows who confirmed what.
      const body = inputs.length ? values : Object.fromEntries(Object.entries(fields).map(([k, v]) => [k, String(v)]));
      note.textContent = 'Confirming...';
      try {
        const res = await window.LabelLensActions.confirmExtraction(d.version_id, body);
        renderExtraction(container, res);
        const n = container.querySelector('#d4Note');
        if (n) n.textContent = 'Extraction confirmed.';
      } catch (e) { note.textContent = 'Confirm failed: ' + e.message; }
    });
    const runBtn = container.querySelector('#btnRunInspectionNow');
    if (runBtn) runBtn.addEventListener('click', async () => {
      if (!isApi()) { goto('D4 Inspect', 'success'); return; }
      note.textContent = 'Running the checks...';
      try {
        const res = await window.LabelLensActions.inspect(d.version_id, (j) => renderLoading(container, j));
        renderInspection(container, res);
      } catch (e) { renderExtraction(container, d); container.querySelector('#d4Note').textContent = 'Inspection failed: ' + e.message; }
    });
  }

  function renderInspection(container, d) {
    const findings = d.findings || [];
    const isPassed = d.passed === true;
    const needsHuman = d.needs_human_count || 0;
    const coverage = d.coverage || [];
    container.innerHTML = `
      ${banner(d)}
      <div class="flex-between" style="margin-bottom: 16px; align-items: flex-start;">
        <div>
          <div class="flex-row" style="gap: 8px;">
            <h2>Label review</h2>
            <span class="badge ${isPassed ? 'badge-teal' : 'badge-danger'}" data-testid="inspect-outcome">${isPassed ? 'No critical findings' : `${d.critical_count || 0} critical finding(s)`}</span>
            ${needsHuman ? `<span class="badge badge-warning" data-testid="needs-human-badge">${needsHuman} need a person</span>` : ''}
          </div>
          <div class="text-xs text-muted" style="margin-top: 4px;">
            Check <code>${esc(d.check_id)}</code> | Label <code>${esc(d.label_id)}</code> | Version <code>${esc(d.version_id)}</code> | Kind ${esc(d.kind)}
          </div>
        </div>
        <div class="flex-row" style="gap: 8px;">
          <button class="btn btn-sm btn-secondary" type="button" id="btnGoToChanges">Create a change &rarr;</button>
          <button class="btn btn-sm btn-secondary" type="button" id="btnExportInspectReport">Export &rarr;</button>
        </div>
      </div>

      ${isPassed ? `
        <div class="notice-banner notice-warning" data-testid="passed-note"><div class="notice-icon">i</div><div class="notice-text">No critical finding was raised by the rules that ran. This is not a compliance determination${needsHuman ? `, and ${needsHuman} rule(s) need a person` : ''}.</div></div>` : ''}

      <div class="card">
        <div class="card-header-clean flex-between">
          <span class="font-semibold text-sm">Findings (${findings.length})</span>
          <span class="text-xs text-muted">${d.critical_count || 0} critical, ${d.review_count || 0} review, ${d.info_count || 0} info</span>
        </div>
        <div class="flex-col" style="gap: 12px;">
          ${findings.length === 0 ? '<div class="text-sm text-muted">No problem findings.</div>' : findings.map(f => `
            <div style="border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px; background: var(--color-bg-subtle);" data-testid="finding">
              <div class="flex-between">
                <div class="flex-row" style="gap: 6px;">
                  <span class="badge ${f.severity === 'critical' ? 'badge-danger' : (f.severity === 'review' ? 'badge-warning' : 'badge-blue')}">${esc(f.severity)}</span>
                  <span class="font-semibold text-xs">${esc(kindText(f.kind))}</span>
                  ${f.needs_human ? '<span class="badge badge-warning">needs a person</span>' : ''}
                </div>
                <span class="text-xs text-muted">${f.rule_id ? 'Rule <code>' + esc(f.rule_id) + '</code> | ' : ''}Field <code>${esc(f.field || '')}</code></span>
              </div>
              <div class="text-xs" style="margin-top: 6px;">${esc(f.message)}</div>
              ${f.observed || f.expected ? `<div class="text-xs" style="margin-top: 4px;">Observed <span class="badge badge-danger">${esc(f.observed)}</span> Expected <span class="badge badge-teal">${esc(f.expected)}</span></div>` : ''}
              ${(f.citations || []).map(c => `
                <div style="margin-top: 8px; padding: 8px; background: #ffffff; border-radius: 4px; border: 1px solid var(--color-border); font-size: 0.75rem;" data-testid="citation">
                  <div class="flex-between">
                    <span class="font-semibold"><span class="badge badge-teal">${esc(c.source_type || 'cfr')}</span> 21 CFR ${esc(c.section)}: ${esc(c.title)}</span>
                    ${c.url ? `<a href="${esc(c.url)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-secondary" style="font-size: 0.7rem; padding: 1px 6px;">View regulation &rarr;</a>` : ''}
                  </div>
                  ${c.quote ? `<div style="font-style: italic; margin-top: 4px; border-left: 2px solid var(--color-primary-teal); padding-left: 8px;">"${esc(c.quote)}"</div>` : ''}
                </div>`).join('')}
            </div>`).join('')}
        </div>
      </div>

      ${coverage.length ? `
        <div class="card" style="margin-top: 16px;" data-testid="coverage">
          <div class="card-header-clean font-semibold text-sm">Rule coverage (${coverage.length} rules)</div>
          <div class="flex-col" style="gap: 2px;">
            ${coverage.map(c => `<div class="flex-between text-xs"><span class="font-mono">${esc(c.rule_id)}</span><span class="badge ${c.outcome === 'pass' ? 'badge-teal' : (c.outcome === 'needs_human' ? 'badge-warning' : (c.outcome === 'fail' ? 'badge-danger' : 'badge-blue'))}">${esc(c.outcome)}</span><span class="text-muted" style="flex: 1; margin-left: 12px;">${esc(c.reason || '')}</span></div>`).join('')}
          </div>
        </div>` : ''}`;

    container.querySelector('#btnExportInspectReport').addEventListener('click', () => goto('D8 Export'));
    container.querySelector('#btnGoToChanges').addEventListener('click', () => goto('D6 Changes'));
  }

  function renderScreenD4(container, state, meta, data) {
    if (!container) return;
    const d = data || {};
    if (d.job_id && d.kind) { renderLoading(container, d); return; }
    if (d.findings) { renderInspection(container, d); return; }
    if (d.fields) { renderExtraction(container, d); return; }
    container.innerHTML = `${banner(d)}<div class="card" style="text-align:center;padding:32px;"><h3>Nothing to show</h3><p class="text-muted text-sm">No extraction or check result for this state.</p></div>`;
  }

  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D4 Inspect'] = renderScreenD4;
  window.LabelLensRenderers['D4'] = renderScreenD4;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD4 };
  }
})();
