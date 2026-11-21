/**
 * ui/js/public-scan.js
 * Public photo scan (api mode): take or upload a photo of a medicine pack, send it to publicScan, show what the
 * server read and what it could or could not identify.
 *
 * - "Take a photo": getUserMedia with a live preview, Capture and Retake on a desktop browser (works on localhost
 *   and 127.0.0.1, which are secure contexts); on a phone, or where getUserMedia is not available (for example a
 *   LAN address without HTTPS), the file input with capture="environment" opens the phone camera instead.
 * - Every photo is downscaled to a long side of 1600 px and sent as JPEG.
 * - The server runs the quality gate (retake_photo with reasons), reads every text line and matches the text with
 *   the reference medicines. Nothing is shown as an answer that the server did not accept or the person did not pick.
 * - Public medicine mode only. No em dashes.
 */
(function () {
  const MAX_SIDE = 1600;
  const JPEG_QUALITY = 0.9;
  const RETAKE_HELP = {
    blur: 'The photo is blurry. Hold the phone still and let it focus on the pack before taking the photo.',
    low_contrast: 'The text is hard to see. Use more light and avoid shadows across the pack.',
    glare: 'There is glare on the pack. Tilt it a little so the light does not reflect into the camera.',
  };

  function esc(s) {
    if (window.LabelLensData && window.LabelLensData.escapeHtml) return window.LabelLensData.escapeHtml(s);
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  const isApi = () => window.LabelLensData && window.LabelLensData.CONFIG.mode === 'api';
  const isPhone = () => !!(window.matchMedia && window.matchMedia('(pointer: coarse)').matches &&
    /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent));
  const canStream = () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.isSecureContext);

  /** Draw a bitmap or video frame on a canvas with the long side at most MAX_SIDE and return a JPEG blob. */
  function toJpeg(source, width, height) {
    const scale = Math.min(1, MAX_SIDE / Math.max(width, height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(width * scale));
    canvas.height = Math.max(1, Math.round(height * scale));
    canvas.getContext('2d').drawImage(source, 0, 0, canvas.width, canvas.height);
    return new Promise((resolve, reject) => {
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('The photo could not be prepared.'))), 'image/jpeg', JPEG_QUALITY);
    });
  }

  /** A picked file (any image type the browser can decode) as a downscaled JPEG blob. */
  async function fileToJpeg(file) {
    if (window.createImageBitmap) {
      let bitmap;
      try { bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' }); } catch (e) { bitmap = await createImageBitmap(file); }
      const blob = await toJpeg(bitmap, bitmap.width, bitmap.height);
      if (bitmap.close) bitmap.close();
      return blob;
    }
    const url = URL.createObjectURL(file);
    try {
      const img = await new Promise((resolve, reject) => { const i = new Image(); i.onload = () => resolve(i); i.onerror = () => reject(new Error('This file is not an image.')); i.src = url; });
      return await toJpeg(img, img.naturalWidth, img.naturalHeight);
    } finally { URL.revokeObjectURL(url); }
  }

  function cameraError(e) {
    const name = e && e.name;
    if (name === 'NotAllowedError' || name === 'SecurityError') return 'Camera permission was denied. Allow the camera for this page in the browser, or upload a photo instead.';
    if (name === 'NotFoundError' || name === 'OverconstrainedError') return 'No camera was found on this device. Upload a photo instead.';
    if (name === 'NotReadableError') return 'The camera is in use by another program. Close it, or upload a photo instead.';
    return 'The camera could not be started. Upload a photo instead.';
  }

  /** Public scan screen (P1 idle state in api mode). */
  function mount(container) {
    let stream = null;
    const root = document.createElement('div');
    root.setAttribute('data-testid', 'scan-panel');
    root.style.cssText = 'max-width:680px;margin:16px auto 0 auto;';
    root.innerHTML = `
      <div data-testid="scan-stage"></div>
      <div class="text-xs text-muted" data-testid="p1-note" id="p1Note" role="status" aria-live="polite" style="text-align:center;margin-top:10px;"></div>`;
    container.appendChild(root);
    const stage = root.querySelector('[data-testid="scan-stage"]');
    const note = root.querySelector('#p1Note');
    const say = (t) => { note.textContent = t || ''; };

    const stopStream = () => { if (stream) { stream.getTracks().forEach((t) => t.stop()); stream = null; } };
    const hiddenInput = (capture) => {
      const input = document.createElement('input');
      input.type = 'file'; input.accept = 'image/*'; input.style.display = 'none';
      if (capture) input.setAttribute('capture', 'environment');
      input.setAttribute('data-testid', capture ? 'p1-camera-input' : 'p1-file-input');
      root.appendChild(input);
      input.addEventListener('change', async () => {
        const file = input.files && input.files[0];
        input.remove();
        if (!file) return;
        try { send(await fileToJpeg(file), capture ? 'camera' : 'upload'); } catch (e) { say('This file could not be read as a photo. Choose a JPEG or PNG image.'); }
      });
      return input;
    };

    function chooseFile(capture) { hiddenInput(capture).click(); }

    async function openCamera() {
      stopStream();
      say('');
      if (isPhone() || !canStream()) {
        say(isPhone() ? '' : 'Live camera preview needs a secure page (localhost or HTTPS). Choose a photo from this device instead.');
        chooseFile(true);
        return;
      }
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 } }, audio: false });
      } catch (e) {
        say(cameraError(e));
        return;
      }
      stage.innerHTML = `
        <div class="card" data-testid="camera-panel" style="padding:12px;">
          <video data-testid="camera-video" autoplay playsinline muted style="width:100%;border-radius:8px;background:#0f172a;"></video>
          <div class="flex-row" style="justify-content:center;gap:12px;margin-top:12px;">
            <button class="btn btn-primary" type="button" data-testid="camera-capture">Capture</button>
            <button class="btn btn-secondary" type="button" data-testid="camera-cancel">Cancel</button>
          </div>
        </div>`;
      const video = stage.querySelector('video');
      video.srcObject = stream;
      stage.querySelector('[data-testid="camera-cancel"]').addEventListener('click', () => { stopStream(); idle(); });
      stage.querySelector('[data-testid="camera-capture"]').addEventListener('click', async () => {
        if (!video.videoWidth) { say('The camera is still starting. Try again in a second.'); return; }
        try { review(await toJpeg(video, video.videoWidth, video.videoHeight)); } catch (e) { say(e.message); }
      });
    }

    /** Show the captured frame with Retake and Use this photo before anything is sent. */
    function review(blob) {
      stopStream();
      const url = URL.createObjectURL(blob);
      stage.innerHTML = `
        <div class="card" data-testid="capture-review" style="padding:12px;">
          <img alt="Captured photo of the pack" src="${url}" style="width:100%;border-radius:8px;">
          <div class="flex-row" style="justify-content:center;gap:12px;margin-top:12px;">
            <button class="btn btn-primary" type="button" data-testid="capture-use">Use this photo</button>
            <button class="btn btn-secondary" type="button" data-testid="capture-retake">Retake</button>
          </div>
        </div>`;
      stage.querySelector('[data-testid="capture-retake"]').addEventListener('click', () => { URL.revokeObjectURL(url); openCamera(); });
      stage.querySelector('[data-testid="capture-use"]').addEventListener('click', () => { URL.revokeObjectURL(url); send(blob, 'camera'); });
    }

    function idle() { stage.innerHTML = ''; }

    async function send(blob, source) {
      stage.innerHTML = `
        <div class="card" data-testid="scan-progress" style="text-align:center;padding:24px;">
          <div class="spinner" aria-hidden="true"></div>
          <h3 style="margin-top:8px;">Reading the pack</h3>
          <p class="text-muted text-sm" id="p1Progress" style="margin-top:6px;">Uploading the photo.</p>
          <p class="text-xs text-muted" style="margin-top:6px;">This can take up to a minute. The text on the pack is read line by line.</p>
        </div>`;
      const progress = stage.querySelector('#p1Progress');
      say('');
      try {
        const res = await window.LabelLensActions.publicScan(blob, (j) => { progress.textContent = `Status: ${j.state}${j.message ? ' (' + j.message + ')' : ''}`; }, source);
        showOutcome(res);
      } catch (e) {
        failedPanel('The scan could not be started', e.message);
      }
    }

    function failedPanel(title, message, reasons) {
      const help = (reasons || []).map((r) => `<li>${esc(RETAKE_HELP[r] || r)}</li>`).join('');
      stage.innerHTML = `
        <div class="notice-banner notice-warning" data-testid="scan-failed">
          <div class="notice-icon">i</div>
          <div>
            <div class="notice-title">${esc(title)}</div>
            <div class="notice-text">${esc(message || '')}</div>
            ${help ? `<ul class="text-sm" data-testid="retake-reasons" style="margin:8px 0 0 18px;">${help}</ul>` : ''}
          </div>
        </div>
        <div class="flex-row" style="justify-content:center;gap:12px;margin-top:12px;">
          <button class="btn btn-primary" type="button" data-testid="retake">Take another photo</button>
          <button class="btn btn-secondary" type="button" data-testid="upload-instead">Upload a photo</button>
        </div>
        ${typeNameHtml()}`;
      stage.querySelector('[data-testid="retake"]').addEventListener('click', openCamera);
      stage.querySelector('[data-testid="upload-instead"]').addEventListener('click', () => chooseFile(false));
      bindTypeName(stage);
    }

    function showOutcome(res) {
      const job = res.job || {};
      if (job.state === 'failed') {
        const err = job.error || {};
        if (err.error === 'retake_photo') {
          failedPanel('Retake the photo', err.message, (err.details && err.details.reasons) || []);
        } else if (err.error === 'busy') {
          failedPanel('Busy right now', err.message);
        } else {
          failedPanel('The photo could not be read', err.message || 'Try again, or type the name.');
        }
        return;
      }
      if (!res.result) { failedPanel('No result', 'The server did not return a result. Try again, or type the name.'); return; }
      showMatch(res.result);
    }

    stage.innerHTML = '';
    root.openCamera = openCamera;
    root.chooseFile = chooseFile;
    root.stopStream = stopStream;
    return root;
  }

  /** Render a PublicMatchResult on the P2 screen (state from the outcome) and mark its nav tab. */
  function showMatch(body) {
    const state = body.outcome === 'matched' ? 'success' : body.outcome === 'needs_review' ? 'needs_review' : 'empty';
    document.querySelectorAll('.public-nav-btn[data-screen]').forEach((b) => {
      b.classList.toggle('active', b.dataset.screen === 'P2 Product information');
    });
    window.dispatchEvent(new CustomEvent('labellens:state-changed', {
      detail: { screen: 'P2 Product information', state, meta: {}, data: body },
    }));
  }

  function typeNameHtml() {
    return `
      <div class="card" data-testid="type-name" style="margin-top:16px;padding:16px;text-align:left;">
        <div class="font-semibold text-sm">Type the name instead</div>
        <p class="text-xs text-muted" style="margin:4px 0 8px 0;">Type the medicine name as printed on the pack, for example the brand or the active ingredient.</p>
        <div class="flex-row" style="gap:8px;">
          <input type="text" id="p1TypedName" data-testid="type-name-input" aria-label="Medicine name" maxlength="200" placeholder="Medicine name" style="flex:1;padding:8px 10px;border:1px solid var(--color-border);border-radius:8px;font:inherit;">
          <button class="btn btn-secondary" type="button" data-testid="type-name-go">Find</button>
        </div>
        <div class="text-xs text-muted" data-testid="type-name-note" style="margin-top:6px;"></div>
      </div>`;
  }

  function bindTypeName(scope) {
    const input = scope.querySelector('[data-testid="type-name-input"]');
    const go = scope.querySelector('[data-testid="type-name-go"]');
    const noteEl = scope.querySelector('[data-testid="type-name-note"]');
    if (!input || !go) return;
    const run = async () => {
      const name = input.value.trim();
      if (!name) { noteEl.textContent = 'Type a name first.'; return; }
      noteEl.textContent = 'Looking up...';
      try {
        const r = await window.LabelLensApi.request('POST', '/public/match', { json: { product_name: name } });
        if (r.status !== 200) { noteEl.textContent = (r.body && r.body.message) || `The lookup failed (HTTP ${r.status}).`; return; }
        showMatch(r.body);
      } catch (e) { noteEl.textContent = e.message; }
    };
    go.addEventListener('click', run);
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') run(); });
  }

  /** The evidence card: every line read from the photo, the ones behind the match marked. */
  function evidenceHtml(body) {
    const lines = body.read_lines || [];
    if (!lines.length) return '';
    const items = lines.map((l) => `
      <li data-testid="read-line"${l.used ? ' data-used="true"' : ''} style="padding:2px 0;${l.used ? 'font-weight:600;' : ''}">
        ${esc(l.text)}
        ${l.used ? '<span class="badge badge-teal" style="margin-left:6px;">used for the match</span>' : ''}
      </li>`).join('');
    return `
      <details class="card" data-testid="scan-evidence" ${body.outcome === 'matched' ? '' : 'open'} style="margin-top:16px;padding:12px 16px;">
        <summary class="font-semibold text-sm">What we read on the pack (${lines.length} line${lines.length === 1 ? '' : 's'})</summary>
        ${body.matched_text ? `<p class="text-xs text-muted" style="margin:8px 0;">Matched text: <strong>${esc(body.matched_text)}</strong></p>` : ''}
        <ul style="list-style:none;padding:0;margin:8px 0 0 0;" class="text-sm">${items}</ul>
        <p class="text-xs text-muted" style="margin-top:8px;">Text is read by software and can contain mistakes.</p>
      </details>`;
  }

  /** Wrap the P2 renderer: add the evidence card and, when nothing was identified, the type-the-name box. */
  function decorateP2(container, state, data) {
    const body = data || {};
    const fromScan = Array.isArray(body.read_lines);
    const askName = isApi() && (state === 'empty' || (fromScan && state === 'needs_review'));
    if (!fromScan && !askName) return;
    const extra = document.createElement('div');
    extra.setAttribute('data-testid', 'scan-extra');
    extra.style.cssText = 'max-width:640px;margin:0 auto;';
    let html = '';
    if (fromScan) {
      if (body.outcome === 'no_reference_match') {
        const text = body.message || 'This product is not one of the reference labels.';
        html += `<div class="notice-banner notice-warning" data-testid="not-identified" style="margin-top:16px;"><div class="notice-icon">i</div><div><div class="notice-title">${body.reason === 'timeout' ? 'The photo took too long to read' : 'Not identified'}</div><div class="notice-text">${esc(text)}</div></div></div>`;
      }
      html += evidenceHtml(body);
    }
    if (askName) {
      html += typeNameHtml();
      html += `<div class="flex-row" style="justify-content:center;margin-top:12px;"><button class="btn btn-primary" type="button" data-testid="scan-again">Scan another photo</button></div>`;
    }
    extra.innerHTML = html;
    container.appendChild(extra);
    bindTypeName(extra);
    const again = extra.querySelector('[data-testid="scan-again"]');
    if (again) again.addEventListener('click', () => {
      document.querySelectorAll('.public-nav-btn[data-screen]').forEach((b) => {
        b.classList.toggle('active', b.dataset.screen === 'P1 Scan and Understand');
      });
      if (window.LabelLensStateSwitcher) window.LabelLensStateSwitcher.setScreen('P1 Scan and Understand', 'empty (idle)');
    });
  }

  function wrapP2() {
    const renderers = window.LabelLensRenderers || {};
    ['P2 Product information', 'P2'].forEach((key) => {
      const base = renderers[key];
      if (typeof base !== 'function' || base.__scanWrapped) return;
      const wrapped = (container, state, meta, data) => { base(container, state, meta, data); decorateP2(container, state, data); };
      wrapped.__scanWrapped = true;
      renderers[key] = wrapped;
    });
  }
  wrapP2();

  window.LabelLensPublicScan = { mount, showMatch, evidenceHtml, fileToJpeg, toJpeg, MAX_SIDE };
})();
