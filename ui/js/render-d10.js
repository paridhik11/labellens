/**
 * ui/js/render-d10.js
 * Renderer for Screen D10: Print verification
 *
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Outcomes are shown as the API names them: match, mismatch, rescan_needed.
 *   The UI never uses the word "verified", and a rescan is never shown as a pass.
 * - Never invent data.
 * - No em dashes.
 */

(function() {
  const esc = (s) => window.LabelLensData.escapeHtml(s);

  function pct(x) {
    return typeof x === 'number' ? Math.round(x * 100) + '%' : 'N/A';
  }

  function renderLoading(container, d) {
    const progress = typeof d.progress === 'number' ? d.progress : 0;
    container.innerHTML = `
      <div class="card" data-testid="pv-loading" style="text-align: center; padding: 48px; max-width: 600px; margin: 0 auto;">
        <div class="text-xs font-semibold text-muted" style="margin-bottom: 8px;">Job <code>${esc(d.job_id)}</code> | ${esc(d.state)}</div>
        <h3>Comparing the printed photo with the approved artwork</h3>
        <p class="text-muted text-sm" style="margin-top: 8px;">${esc(d.message || '')}</p>
        <div style="width: 280px; height: 6px; background: #e2e8f0; border-radius: 99px; margin: 24px auto; overflow: hidden;">
          <div style="width: ${Math.round(progress * 100)}%; height: 100%; background: var(--color-primary-blue);"></div>
        </div>
        <div class="text-xs text-muted">${pct(progress)}</div>
      </div>`;
  }

  function renderScreenD10(container, state, meta, data) {
    if (!container) return;
    const d = data || {};

    if (d.job_id && d.kind === 'print_verify') {
      renderLoading(container, d);
      return;
    }

    if (d.items && d.items.length === 0) {
      container.innerHTML = `
        <div style="margin-bottom: 16px;">
          <h2>Print verification</h2>
          <div class="text-xs text-muted">Version: <code>${esc(d.version_id || '')}</code></div>
        </div>
        <div class="card" data-testid="pv-empty" style="text-align: center; padding: 48px;">
          <h3>No print checks on record</h3>
          <p class="text-muted text-sm" style="margin-top: 8px;">Photograph a printed label of an approved version to compare it with the approved artwork.</p>
        </div>`;
      return;
    }

    const outcome = d.outcome;
    const isMatch = outcome === 'match';
    const isRescan = outcome === 'rescan_needed';
    const isMismatch = outcome === 'mismatch';
    const mismatches = d.mismatches || [];
    const quality = d.quality || {};
    const barcode = d.barcode || {};
    const badgeCls = isMatch ? 'badge-teal' : (isRescan ? 'badge-warning' : 'badge-danger');
    const badgeText = isMatch ? 'MATCH' : (isRescan ? 'RESCAN NEEDED' : (isMismatch ? 'MISMATCH' : esc(String(outcome).toUpperCase())));

    let resultBody;
    if (mismatches.length > 0) {
      resultBody = `<div class="flex-col" style="gap: 10px;">${mismatches.map(m => `
        <div class="card" data-testid="pv-mismatch" style="border: 1px solid var(--color-border); padding: 12px;">
          <div class="font-semibold text-xs" style="color: var(--color-danger-text);">${esc(m.field || 'field')} differs</div>
          <div class="kv-table" style="margin-top: 6px;">
            <div class="kv-row"><span class="kv-label">Observed (print)</span><span class="kv-value"><span class="badge badge-danger">${esc(m.observed)}</span></span></div>
            <div class="kv-row"><span class="kv-label">Expected (approved)</span><span class="kv-value"><span class="badge badge-teal">${esc(m.expected)}</span></span></div>
            ${Array.isArray(m.bbox) ? `<div class="kv-row"><span class="kv-label">Box (x, y, w, h px)</span><span class="kv-value font-mono text-xs">${esc(m.bbox.join(', '))}</span></div>` : ''}
          </div>
        </div>`).join('')}</div>`;
    } else if (isRescan) {
      resultBody = `<div class="text-sm" data-testid="pv-no-result" style="padding: 16px; text-align: center;">
        <div class="font-semibold">No result: the photo could not be compared.</div>
        <div class="text-muted" style="margin-top: 6px;">Nothing was matched and nothing was found different. Retake the photo.</div></div>`;
    } else {
      resultBody = `<div class="text-sm" style="padding: 16px; text-align: center;">
        <div class="font-semibold">No differences found in the compared fields.</div>
        <div class="text-muted" style="margin-top: 6px;">This is a comparison with the approved artwork. It is not a compliance determination.</div></div>`;
    }

    container.innerHTML = `
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Print check: <code>${esc(d.verification_id)}</code></h2>
          <div class="text-xs text-muted">Version: <code>${esc(d.version_id)}</code> | Condition: <span class="badge badge-blue">${esc(d.condition)}</span> | Photo <code title="${esc((d.photo_file || {}).sha256)}">${esc(String((d.photo_file || {}).sha256 || '').slice(0, 12))}...</code></div>
        </div>
        <span class="badge ${badgeCls}" data-testid="pv-outcome" data-outcome="${esc(outcome)}">${badgeText}</span>
      </div>

      ${isRescan ? `
        <div class="notice-banner notice-warning" data-testid="pv-rescan">
          <div class="notice-icon">i</div>
          <div>
            <div class="notice-title">Rescan needed: the photo is not good enough to compare</div>
            <div class="notice-text">${esc(d.rescan_reason || 'Retake the photo.')}</div>
          </div>
        </div>` : ''}

      ${isMismatch ? `
        <div class="notice-banner notice-danger" data-testid="pv-mismatch-banner">
          <div class="notice-icon">!</div>
          <div>
            <div class="notice-title">Mismatch: the print differs from the approved artwork</div>
            <div class="notice-text">${mismatches.length} field${mismatches.length === 1 ? '' : 's'} differ. Do not release this print run until a person has checked it.</div>
          </div>
        </div>` : ''}

      ${isMatch ? `
        <div class="notice-banner notice-warning" data-testid="pv-match-note">
          <div class="notice-icon">i</div>
          <div>
            <div class="notice-title">Match on the compared fields</div>
            <div class="notice-text">The photo agrees with the approved artwork on the fields and barcode compared. A person still signs off the print.</div>
          </div>
        </div>` : ''}

      <div class="grid-two-col">
        <div class="card">
          <div class="card-header-clean font-semibold text-sm">Text comparison</div>
          ${resultBody}
        </div>

        <div class="card">
          <div class="card-header-clean font-semibold text-sm">2D barcode</div>
          <div class="kv-table">
            <div class="kv-row"><span class="kv-label">Decoded</span><span class="kv-value">${barcode.decoded ? '<span class="badge badge-teal">Yes</span>' : '<span class="badge badge-warning">Not decoded</span>'}</span></div>
            <div class="kv-row"><span class="kv-label">Matches expected</span><span class="kv-value">${barcode.decoded ? `<span class="badge ${barcode.match ? 'badge-teal' : 'badge-danger'}">${barcode.match ? 'Yes' : 'No'}</span>` : '<span class="text-muted text-xs">not compared</span>'}</span></div>
            <div class="kv-row"><span class="kv-label">Expected payload</span><span class="kv-value font-mono text-xs" style="word-break: break-all;">${esc(barcode.expected_payload || '')}</span></div>
            ${barcode.decoded ? `
              <div class="kv-row"><span class="kv-label">Symbology</span><span class="kv-value">${esc(barcode.decoded.type)}</span></div>
              <div class="kv-row"><span class="kv-label">Raw data</span><span class="kv-value font-mono text-xs" style="word-break: break-all;">${esc(barcode.decoded.raw)}</span></div>` : ''}
          </div>

          <div style="margin-top: 16px; border-top: 1px solid var(--color-border); padding-top: 12px;">
            <div class="text-xs font-semibold text-muted" style="margin-bottom: 6px;">Photo quality</div>
            <div class="flex-row" style="gap: 16px;">
              <span class="text-xs">Blur: <strong>${quality.blur !== undefined ? esc(quality.blur) : 'N/A'}</strong></span>
              <span class="text-xs">Glare: <strong>${quality.glare !== undefined ? esc(quality.glare) : 'N/A'}</strong></span>
              <span class="text-xs">Confidence: <strong>${pct(quality.confidence)}</strong></span>
            </div>
          </div>
        </div>
      </div>`;
  }

  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D10 Print verification'] = renderScreenD10;
  window.LabelLensRenderers['D10'] = renderScreenD10;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD10 };
  }
})();
