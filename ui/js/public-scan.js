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
        <div class="card" data-testid="scan-progress" role="status" aria-live="polite" style="text-align:center;padding:24px;">
          <div class="spinner" data-testid="scan-spinner" aria-hidden="true"></div>
          <h3 style="margin-top:12px;">Reading the pack</h3>
          <p class="text-sm" style="margin-top:6px;font-weight:600;">Reading can take up to a minute. Please keep this page open.</p>
          <p class="text-muted text-sm" id="p1Progress" style="margin-top:6px;">Uploading the photo.</p>
          <p class="text-xs text-muted" style="margin-top:6px;" data-testid="scan-elapsed">0 s</p>
        </div>`;
      const progress = stage.querySelector('#p1Progress');
      const elapsed = stage.querySelector('[data-testid="scan-elapsed"]');
      const began = Date.now();
      const tick = setInterval(() => {
        if (!elapsed.isConnected) { clearInterval(tick); return; }
        elapsed.textContent = `${Math.round((Date.now() - began) / 1000)} s`;
      }, 1000);
      say('');
      try {
        const res = await window.LabelLensActions.publicScan(blob, (j) => { progress.textContent = `Status: ${j.state}${j.message ? ' (' + j.message + ')' : ''}`; }, source);
        clearInterval(tick);
        showOutcome(res);
      } catch (e) {
        clearInterval(tick);
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

  function typeNameHtml(prefill) {
    return `
      <div class="card" data-testid="type-name" style="margin-top:16px;padding:16px;text-align:left;">
        <div class="font-semibold text-sm">Type the name instead</div>
        <p class="text-xs text-muted" style="margin:4px 0 8px 0;">Type the medicine name as printed on the pack, for example the brand or the active ingredient.</p>
        <div class="flex-row" style="gap:8px;">
          <input type="text" id="p1TypedName" data-testid="type-name-input" aria-label="Medicine name" maxlength="200" placeholder="Medicine name" value="${esc(prefill || '')}" style="flex:1;padding:8px 10px;border:1px solid var(--color-border);border-radius:8px;font:inherit;">
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
        if (window.LabelLensLive) window.LabelLensLive.setLastName(name);
        showMatch(r.body);
      } catch (e) { noteEl.textContent = e.message; }
    };
    go.addEventListener('click', run);
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') run(); });
  }


  // ---------------------------------------------------------------- name from the photo text (no NDC, not in the 30)

  // Words that are on most packs and never name the medicine: pack words, colours, Spanish instructions, salts
  // ("metoprolol" finds the label, "tartrate" alone finds many unrelated ones) and common labeler words.
  const NAME_STOP = new Set(('tablet tablets capsule capsules caplet caplets only each contains contain keep reach children '
    + 'store storage stored usp film coated extended release delayed oral solution suspension injection cream ointment '
    + 'dosage prescription pharmacist directions direction warning warnings synthetic test image label labels manufactured '
    + 'distributed marketed packaged pharma pharmaceuticals pharmaceutical laboratories limited corp incorporated '
    + 'hydrochloride sodium calcium potassium tartrate succinate maleate citrate phosphate sulfate acetate besylate '
    + 'mesylate fumarate hyclate bromide chloride magnesium package insert information patient medication guide daily '
    + 'times every hours count bottle blister carton strength active inactive ingredients ingredient purpose relief adult '
    + 'adults years older under doctor before after using other questions comments call toll free made india china '
    + 'canada dayton jersey usual dispense dispensed container tight light moisture temperature room controlled excursions '
    + 'permitted protect between below above should while taking alcohol caution federal prohibits english espanol '
    + 'instrucciones dirigido directed please provided separately drugs batch expiration coating stamping varnish paper '
    + 'plastic shake sample master major green white yellow orange black brown purple violet round oval scored '
    + 'see full prescribing lot exp expiry date serial generic brand equivalent compare drug facts uses tamper evident '
    + 'regular extra pain attention physician recommended inhalation tablets each unit dose repack remedy').split(' '));
  const STRENGTH = /\d\s*(mg|mcg|g|ml|%)\b/i;

  /**
   * Up to three words that may name the medicine, best first: letters only, 5 to 14 long (longer ones are words the
   * reader ran together), not a common pack word, from lines the reader was sure of (confidence 0.8 or more).
   * Only words within two lines of a strength ("50 mg"); words written in capitals and on earlier lines come first.
   */
  function guessNames(lines) {
    const scored = new Map();
    const list = lines || [];
    list.forEach((l, i) => {
      if (l.confidence !== undefined && l.confidence < 0.8) return;
      const near = [list[i - 2], list[i - 1], l, list[i + 1], list[i + 2]].some((x) => x && STRENGTH.test(String(x.text || '')));
      if (!near) return; // a medicine name sits next to its strength; elsewhere common words ("drink alcohol") get in
      String(l.text || '').split(/[^A-Za-z]+/).forEach((w) => {
        const low = w.toLowerCase();
        if (low.length < 5 || low.length > 14 || NAME_STOP.has(low)) return;
        const score = (near ? 2 : 0) + (w === w.toUpperCase() ? 1 : 0) + Math.max(0, 1 - i / 20) + Math.min(low.length, 12) / 24;
        if (!scored.has(low) || scored.get(low).score < score) scored.set(low, { word: w, score });
      });
    });
    return [...scored.values()].sort((a, b) => b.score - a.score).slice(0, 3).map((x) => x.word);
  }

  /**
   * True when a DailyMed list entry's product or generic name starts with the word (never the labeler, never a word
   * in the middle: "PHARMACY" must not propose "GOOD NEIGHBOR PHARMACY NASAL ALLERGY").
   */
  function namesWord(c, word) {
    const w = word.toLowerCase();
    return [c.product_name, c.generic_name].some((t) => String(t || '').toLowerCase().split(/[^a-z]+/).filter(Boolean)[0] === w);
  }

  /** Search DailyMed for the guessed words in order; the labels that name the first word with any result. */
  async function lookupByName(words) {
    for (const word of words) {
      let r;
      try { r = await window.LabelLensApi.request('POST', '/public/live/search', { json: { product_name: word } }); } catch (e) { return { error: 'This page could not reach its server.' }; }
      if (r.status !== 200 || !r.body || r.mock) return { error: (r.body && r.body.message) || `The lookup failed (HTTP ${r.status}).` };
      if (r.body.outcome === 'unavailable') return { error: r.body.message || 'DailyMed lookup is not available.' };
      const list = (r.body.candidates || []).filter((c) => namesWord(c, word));
      if (list.length) return { word, list };
    }
    return { word: words[0] || '', list: [] };
  }

  /** "Is this X?" for the next DailyMed label, or "We couldn't identify this pack" with the read name prefilled. */
  function proposeLive(host, found, index) {
    const c = found.list[index];
    if (!c) {
      host.innerHTML = `<div class="notice-banner notice-warning" data-testid="not-identified" style="margin-top:16px;"><div class="notice-icon">i</div><div>
        <div class="notice-title">We couldn't identify this pack</div>
        <div class="notice-text">${found.word ? `We read <strong>${esc(found.word)}</strong> on the pack, but no label was confirmed for it. ` : 'No medicine name could be read from the photo. '}Type the name as printed on the pack, or scan another photo.</div></div></div>
        ${typeNameHtml(found.word)}`;
      bindTypeName(host);
      return;
    }
    const name = [c.product_name || c.title, c.generic_name ? `(${c.generic_name})` : '', c.dosage_form || ''].filter(Boolean).join(' ');
    host.innerHTML = `<div data-testid="live-proposal" data-setid="${esc(c.setid)}">
      <div class="notice-banner" style="margin-top:16px;"><div class="notice-icon">?</div><div>
        <div class="notice-title">Is this ${esc(name)}?</div>
        <div class="notice-text">We read <strong>${esc(found.word)}</strong> on the pack. It is not one of the 30 curated medicines, so DailyMed was searched for that name; this is a label it lists${c.labeler ? ` (from ${esc(c.labeler)})` : ''}. Check it against your pack before anything is shown.</div>
      </div></div>
      <div class="flex-row" style="justify-content:center;gap:8px;margin-top:16px;flex-wrap:wrap;">
        <button class="btn btn-primary" type="button" data-testid="live-confirm">Confirm</button>
        <button class="btn btn-secondary" type="button" data-testid="live-reject">Not this one</button>
        <button class="btn btn-secondary" type="button" data-testid="live-typename">Type the name</button>
      </div>
      <div data-testid="live-fetch-area"></div><div data-testid="live-more"></div></div>`;
    host.querySelector('[data-testid="live-confirm"]').addEventListener('click', () => {
      host.querySelectorAll('button').forEach((b) => { b.disabled = true; });
      window.LabelLensLive.fetchCandidate(c, found.word, host.querySelector('[data-testid="live-fetch-area"]'));
    });
    host.querySelector('[data-testid="live-reject"]').addEventListener('click', () => proposeLive(host, found, index + 1));
    host.querySelector('[data-testid="live-typename"]').addEventListener('click', () => {
      const more = host.querySelector('[data-testid="live-more"]');
      more.innerHTML = typeNameHtml(found.word);
      bindTypeName(more);
    });
  }

  /** No NDC and no curated match: take the name from the photo text and look it up on DailyMed (never auto-confirmed). */
  async function lookupFromPhoto(host, body) {
    const words = guessNames(body.read_lines || []);
    if (!words.length || !window.LabelLensLive || !window.LabelLensLive.fetchCandidate) { proposeLive(host, { word: words[0] || '', list: [] }, 0); return; }
    host.innerHTML = `<p class="text-sm text-muted" data-testid="live-photo-searching" style="text-align:center;margin-top:16px;">We read <strong>${esc(words[0])}</strong> on the pack. Searching DailyMed for it...</p>`;
    const found = await lookupByName(words);
    if (found.error) {
      host.innerHTML = `<div class="notice-banner notice-warning" data-testid="not-identified" style="margin-top:16px;"><div class="notice-icon">i</div><div><div class="notice-title">We couldn't identify this pack</div><div class="notice-text">${esc(found.error)} Type the name as printed on the pack.</div></div></div>${typeNameHtml(words[0])}`;
      bindTypeName(host);
      return;
    }
    proposeLive(host, found, 0);
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
    // A photo that matched nothing (or only below the threshold) and was read completely: look the name up on DailyMed.
    const nameLookup = fromScan && isApi() && body.outcome !== 'matched' && body.reason !== 'timeout' && (body.read_lines || []).length > 0;
    if (fromScan) {
      if (body.outcome === 'no_reference_match' && !nameLookup) {
        const text = body.reason === 'timeout' ? (body.message || 'The photo took too long to read.') : 'No medicine name could be read from the photo.';
        html += `<div class="notice-banner notice-warning" data-testid="not-identified" style="margin-top:16px;"><div class="notice-icon">i</div><div><div class="notice-title">${body.reason === 'timeout' ? 'The photo took too long to read' : "We couldn't identify this pack"}</div><div class="notice-text">${esc(text)}</div></div></div>`;
      }
      if (nameLookup) html += '<div data-testid="live-photo"></div>';
      // not identified: the lines read are evidence, but nothing was "used for the match" (no match was accepted)
      html += body.outcome === 'matched' ? evidenceHtml(body)
        : evidenceHtml({ ...body, outcome: nameLookup ? 'matched' : body.outcome, matched_text: '', read_lines: (body.read_lines || []).map((l) => ({ ...l, used: false })) });
    }
    if (askName && !nameLookup) {
      html += typeNameHtml();
      html += `<div class="flex-row" style="justify-content:center;margin-top:12px;"><button class="btn btn-primary" type="button" data-testid="scan-again">Scan another photo</button></div>`;
    }
    extra.innerHTML = html;
    container.appendChild(extra);
    bindTypeName(extra);
    const livePhoto = extra.querySelector('[data-testid="live-photo"]');
    if (livePhoto) lookupFromPhoto(livePhoto, body);
    const again = extra.querySelector('[data-testid="scan-again"]');
    if (again) again.addEventListener('click', () => {
      document.querySelectorAll('.public-nav-btn[data-screen]').forEach((b) => {
        b.classList.toggle('active', b.dataset.screen === 'P1 Scan and Understand');
      });
      if (window.LabelLensStateSwitcher) window.LabelLensStateSwitcher.setScreen('P1 Scan and Understand', 'empty (idle)');
    });
  }

  /**
   * A photo never confirms itself: a matched scan result first asks "Is this <product>?" with the lines that were read
   * as evidence. Only Confirm shows the label information. "Not this one" shows nothing about the product.
   */
  function renderConfirm(container, body) {
    const name = (body.candidates && body.candidates[0] && body.candidates[0].product_name) || 'this product';
    container.innerHTML = `
      <div style="max-width:640px;margin:0 auto;" data-testid="scan-confirm-panel">
        <div class="notice-banner" style="margin-top:16px;"><div class="notice-icon">?</div><div>
          <div class="notice-title">Is this ${esc(name)}?</div>
          <div class="notice-text">We read <strong>${esc(body.matched_text || '')}</strong> on the pack and it matches the reference label for ${esc(name)}. Check it against your pack before anything is shown.</div>
        </div></div>
        ${evidenceHtml({ ...body, outcome: 'needs_review' })}
        <div class="flex-row" style="justify-content:center;gap:8px;margin-top:16px;flex-wrap:wrap;">
          <button class="btn btn-primary" type="button" data-testid="scan-confirm">Confirm</button>
          <button class="btn btn-secondary" type="button" data-testid="scan-reject">Not this one</button>
          <button class="btn btn-secondary" type="button" data-testid="scan-typename">Type the name</button>
        </div>
        <div data-testid="scan-confirm-more"></div>
      </div>`;
    const more = container.querySelector('[data-testid="scan-confirm-more"]');
    const openTyping = (message) => {
      more.innerHTML = `${message ? `<p class="text-sm text-muted" style="text-align:center;margin-top:12px;">${esc(message)}</p>` : ''}${typeNameHtml()}`;
      bindTypeName(more);
    };
    container.querySelector('[data-testid="scan-confirm"]').addEventListener('click', () => {
      body.__confirmed = true;
      showMatch(body);
    });
    container.querySelector('[data-testid="scan-reject"]').addEventListener('click', () => {
      openTyping('Nothing is shown for this product. Type the name, or scan another photo.');
      more.insertAdjacentHTML('beforeend', '<div class="flex-row" style="justify-content:center;margin-top:12px;"><button class="btn btn-primary" type="button" data-testid="scan-again">Scan another photo</button></div>');
      more.querySelector('[data-testid="scan-again"]').addEventListener('click', () => {
        document.querySelectorAll('.public-nav-btn[data-screen]').forEach((btn) => {
          btn.classList.toggle('active', btn.dataset.screen === 'P1 Scan and Understand');
        });
        if (window.LabelLensStateSwitcher) window.LabelLensStateSwitcher.setScreen('P1 Scan and Understand', 'empty (idle)');
      });
    });
    container.querySelector('[data-testid="scan-typename"]').addEventListener('click', () => openTyping(''));
  }

  function wrapP2() {
    const renderers = window.LabelLensRenderers || {};
    ['P2 Product information', 'P2'].forEach((key) => {
      const base = renderers[key];
      if (typeof base !== 'function' || base.__scanWrapped) return;
      const wrapped = (container, state, meta, data) => {
        const scan = data && Array.isArray(data.read_lines) && data.outcome === 'matched' && state === 'success';
        if (scan && !data.__confirmed) { renderConfirm(container, data); return; }
        if (data && Array.isArray(data.read_lines) && state === 'needs_review' && isApi()) {
          // below the match threshold: never list those candidates for a photo; treat it as not identified
          const plain = Object.assign({}, data, { candidates: [] });
          base(container, 'empty', meta, plain);
          decorateP2(container, 'empty', data);
          return;
        }
        base(container, state, meta, data);
        decorateP2(container, state, data);
      };
      wrapped.__scanWrapped = true;
      renderers[key] = wrapped;
    });
  }
  wrapP2();

  window.LabelLensPublicScan = { mount, showMatch, renderConfirm, evidenceHtml, fileToJpeg, toJpeg, MAX_SIDE, guessNames, namesWord };
})();
