/**
 * ui/js/render-d8.js
 * Renderer for Screen D8: Export (Download Package)
 *
 * Hard rules:
 * - Professional workspace only (21 CFR 801, 820, 830).
 * - Every export shows the DRAFT banner: stored files keep the DRAFT mark (CR-22), QR only when published.
 * - Never invent data.
 * - No em dashes.
 */

(function() {
  const esc = (s) => window.LabelLensData.escapeHtml(s);

  function fileCard(title, badgeCls, badgeText, blurb, file, kind) {
    const sha = file.sha256 || file.artifact_sha256 || '';
    const size = file.size_mm ? `${esc(file.size_mm.w)} x ${esc(file.size_mm.h)} mm (physical size)` : '';
    return `
      <div class="card" data-testid="export-${kind}">
        <div class="card-header-clean flex-between">
          <span class="font-semibold text-sm">${esc(title)}</span>
          <span class="badge ${badgeCls}">${esc(badgeText)}</span>
        </div>
        <div class="text-xs text-muted" style="margin-bottom: 8px;">${esc(blurb)}</div>
        ${size ? `<div class="text-xs" style="margin-bottom: 6px;">${size}</div>` : ''}
        <div class="text-xs font-mono" style="word-break: break-all; margin-bottom: 6px;">${esc(file.url || '')}</div>
        <div class="text-xs text-muted" style="word-break: break-all; margin-bottom: 12px;">sha256 <code title="${esc(sha)}">${esc(sha.slice(0, 16))}${sha ? '...' : ''}</code></div>
        <button class="btn btn-sm btn-secondary dl-btn" type="button" style="width: 100%;" data-sha="${esc(sha)}" data-kind="${kind}" data-name="${esc((file.url || kind).split('/').pop())}">Download ${esc(kind.toUpperCase())}</button>
      </div>`;
  }

  /** The publishVersion 201 response: only the pinned page, no file list. */
  function renderPublished(container, d) {
    container.innerHTML = `
      ${window.LabelLensData.renderDraftBanner('Publishing pins a public page to this version. Files still carry the DRAFT mark where draft_watermark is true.')}
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Published page</h2>
          <div class="text-xs text-muted">Version: <code>${esc(d.version_id)}</code> | Label: <code>${esc(d.label_id)}</code></div>
        </div>
        <span class="badge badge-teal">PUBLISHED</span>
      </div>
      <div class="card" data-testid="publish-card">
        <div class="kv-table">
          <div class="kv-row"><span class="kv-label">Page</span><span class="kv-value"><code>${esc(d.page_id)}</code></span></div>
          <div class="kv-row"><span class="kv-label">URL</span><span class="kv-value"><code>${esc(d.url)}</code></span></div>
          <div class="kv-row"><span class="kv-label">QR payload</span><span class="kv-value"><code>${esc(d.qr_payload)}</code></span></div>
          <div class="kv-row"><span class="kv-label">Published at</span><span class="kv-value">${esc(d.published_at)}</span></div>
          <div class="kv-row"><span class="kv-label">Tied to review</span><span class="kv-value"><code>${esc(d.review_id)}</code></span></div>
        </div>
      </div>`;
  }

  function renderScreenD8(container, state, meta, data) {
    if (!container) return;
    const d = data || {};

    if (d.page_id && !d.pdf) {
      renderPublished(container, d);
      return;
    }

    const pdf = d.pdf || {};
    const svg = d.svg || {};
    const report = d.report || {};
    const qr = d.qr || null;
    const published = d.status === 'published';
    const marked = d.draft_watermark === true;

    container.innerHTML = `
      ${window.LabelLensData.renderDraftBanner(
        published
          ? 'An approval record and a published page exist for this version. This banner stays on every export; the draft_watermark flag below says whether the files carry the mark.'
          : 'Not approved yet: exports carry the DRAFT mark and there is no QR code until the version is approved and published.')}
      <div class="flex-between" style="margin-bottom: 16px;">
        <div>
          <h2>Export package</h2>
          <div class="text-xs text-muted">Version: <code>${esc(d.version_id)}</code> | Label: <code>${esc(d.label_id)}</code> | Status: <span class="badge badge-blue">${esc(d.status)}</span></div>
        </div>
        <div class="flex-row" style="gap: 8px;">
          <span class="badge badge-draft">DRAFT EXPORT</span>
          <span class="badge ${marked ? 'badge-warning' : 'badge-blue'}" data-testid="watermark-flag">draft_watermark: ${marked ? 'true (files carry the mark)' : 'false'}</span>
        </div>
      </div>

      <div class="grid-three-col" style="margin-top: 20px;">
        ${fileCard('Print PDF', 'badge-blue', 'PDF', 'Artwork at physical size.', pdf, 'pdf')}
        ${fileCard('Editable SVG', 'badge-purple', 'SVG', 'Template-based vector artwork.', svg, 'svg')}
        ${fileCard('Report', 'badge-teal', 'REPORT', 'Change log and self-check result.', report, 'report')}
      </div>
      <div class="text-xs text-muted" id="downloadNote" style="margin-top: 10px;"></div>

      ${qr ? `
        <div class="card" style="margin-top: 20px;" data-testid="qr-card">
          <div class="card-header-clean font-semibold text-sm">Published page and QR payload</div>
          <div class="flex-row" style="gap: 20px; align-items: center;">
            <div style="background: #ffffff; border: 2px solid #0f172a; padding: 12px; border-radius: var(--radius-md); font-family: monospace; font-size: 0.75rem; text-align: center;">
              <div style="font-size: 2rem;">&#9638;</div>
              <span>[QR: ${esc(qr.qr_payload || qr.url)}]</span>
            </div>
            <div>
              <div class="font-semibold text-sm">Public page <code>${esc(qr.page_id)}</code></div>
              <div class="text-xs text-muted" style="margin-top: 2px;">URL: <code>${esc(qr.url)}</code> | Published: ${esc(qr.published_at)}</div>
              <div class="text-xs text-muted" style="margin-top: 6px;">Tied to review record <code>${esc(qr.review_id)}</code></div>
            </div>
          </div>
        </div>` : `
        <div class="card text-sm text-muted" style="margin-top: 20px;" data-testid="no-qr">No QR code: the version is not published.</div>`}
    `;

    const note = container.querySelector('#downloadNote');
    container.querySelectorAll('.dl-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const actions = window.LabelLensActions;
        if (window.LabelLensData.CONFIG.mode === 'api' && actions && actions.download) {
          note.textContent = 'Downloading...';
          try {
            note.textContent = await actions.download(btn.dataset.sha, btn.dataset.name);
          } catch (e) {
            note.textContent = 'Download failed: ' + e.message;
          }
        } else {
          note.textContent = 'Mock mode: this file does not exist. Switch CONFIG.mode to api to download a real draft.';
        }
      });
    });
  }

  window.LabelLensRenderers = window.LabelLensRenderers || {};
  window.LabelLensRenderers['D8 Export'] = renderScreenD8;
  window.LabelLensRenderers['D8'] = renderScreenD8;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { renderScreenD8 };
  }
})();
