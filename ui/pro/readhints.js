/*
 * ui/pro/readhints.js - what to do with the text lines the label reader found but did not put in a field.
 * Pure functions over the extraction (no DOM, no network), so node can test them (tests/test_readhints_js.py).
 *
 *   lines(ex)                  every OCR line with its confidence, junk marks removed
 *   unassigned(ex, form)       the lines no form value already accounts for
 *   sterilization(lines)       {value, line} from a line such as "STERILE EO", or null
 *   storage(lines)             {value, lines} from "Store at 2-8 C" style lines, or null
 *   modelCandidate(lines)      the single unassigned line that looks like a model or reference number, or null
 *
 * These are plain rules written from how device labels are usually printed. They were not measured on real photos
 * (none is stored on this PC); every value they produce is shown as a suggestion that a person confirms.
 * No em dashes.
 */
(function () {
  const MARKS = /^(DRAFT[, ]|TEST\s*DATA|NOT FOR PRODUCTION)/i;
  const compact = (s) => String(s || '').replace(/\s+/g, '').toUpperCase();

  /** Every OCR line, in reading order, without the DRAFT and TEST DATA marks LabelLens itself prints. */
  function lines(ex) {
    return (ex.ocr_blocks || [])
      .map((b) => ({ text: String(b.text || '').trim(), conf: typeof b.conf === 'number' ? b.conf : null }))
      .filter((l) => l.text && !MARKS.test(l.text));
  }

  /** Lines whose text is not already in a form value (compared without spaces or case, either way round). */
  function unassigned(ex, form) {
    const values = Object.values(form || {}).map(compact).filter((v) => v.length >= 2);
    const bar = (ex.barcodes || []).map((b) => compact(b.raw));
    return lines(ex).filter((l) => {
      const c = compact(l.text);
      if (c.length < 2) return false;
      if (values.some((v) => c === v || (v.length >= 3 && c.includes(v)) || (v.length >= 3 && v.includes(c) && c.length >= 4))) return false;
      if (bar.some((b) => b && b.includes(c))) return false;
      return true;
    });
  }

  const STERILE_METHODS = [
    [/ETHYLENE\s*OXIDE|\bEO\b|\bETO\b|STERILE\s*EO/i, 'EO'],
    [/GAMMA/i, 'gamma'],
    [/IRRADIAT|RADIATION|\bSTERILE\s*R\b/i, 'R'],
    [/STEAM|AUTOCLAV|MOIST\s*HEAT/i, 'steam'],
  ];

  /** "STERILE EO", "Sterilized using irradiation", "NON-STERILE": the method as the record spells it, or the line. */
  function sterilization(ls) {
    for (const l of ls) {
      const t = l.text;
      if (/\bNON[\s-]?STERILE\b/i.test(t)) return { value: 'Non-sterile', line: t };
      if (/\bSTERIL(E|IZED|ISED)\b|\bSTERILI[ZS]ATION\b/i.test(t)) {
        const hit = STERILE_METHODS.find(([re]) => re.test(t));
        return { value: hit ? hit[1] : 'Sterile', line: t };
      }
    }
    return null;
  }

  const STORAGE_RE = /\b(STORE|STORAGE|KEEP\s+(DRY|COOL|AWAY|IN)|PROTECT\s+FROM|REFRIGERAT|HUMIDITY)\b|\d\s*[°º]?\s*C?\s*(-|–|TO)\s*\d+\s*[°º]\s*[CF]\b|\d\s*[°º]\s*[CF]\b/i;

  /** Up to two lines about storage conditions. The word "Storage:" or "Store" at the start is dropped. */
  function storage(ls) {
    const hit = ls.filter((l) => STORAGE_RE.test(l.text) && !/\bSTERIL/i.test(l.text)).slice(0, 2);
    if (!hit.length) return null;
    return { value: hit.map((l) => l.text.replace(/^\s*storage\s*:?\s*/i, '').trim()).join('; '), lines: hit.map((l) => l.text) };
  }

  /** A line shaped like a model or reference number: letters and digits (or a hyphen), no spaces, 3 to 20 characters. */
  function modelCandidate(unassignedLines) {
    const c = unassignedLines.filter((l) => /^[A-Z0-9][A-Z0-9\-/.]{2,19}$/i.test(l.text) && /\d/.test(l.text) && /[A-Z]/i.test(l.text)
      && !/^\d{4}-\d{2}-\d{2}$/.test(l.text) && (l.conf === null || l.conf >= 0.6));
    return c.length === 1 ? c[0] : null;
  }

  /**
   * Merge the readings of several images of one label into one extraction.
   * A field takes the first value that its image did not mark unclear (else the first value). When two images read a
   * field differently, both values are kept in `conflicts` so the page can say so. Barcodes and text lines are joined
   * without repeats. A single reading is returned unchanged.
   */
  function merge(exs) {
    if (exs.length === 1) return exs[0];
    const names = [];
    exs.forEach((ex) => Object.keys(ex.fields || {}).forEach((k) => { if (!names.includes(k)) names.push(k); }));
    const fields = {}; const conflicts = {}; const unclear = [];
    for (const k of names) {
      const cands = exs.map((ex, i) => ({ v: String((ex.fields || {})[k] || '').trim(), clear: !(ex.unclear_fields || []).includes(k), i })).filter((c) => c.v);
      if (!cands.length) continue;
      const pick = cands.find((c) => c.clear) || cands[0];
      fields[k] = pick.v;
      if (!pick.clear) unclear.push(k);
      const distinct = [...new Set(cands.map((c) => compact(c.v)))];
      if (distinct.length > 1) conflicts[k] = cands.map((c) => `${c.v} (image ${c.i + 1})`);
    }
    const seen = new Set(); const barcodes = [];
    exs.forEach((ex) => (ex.barcodes || []).forEach((b) => { if (!seen.has(b.raw)) { seen.add(b.raw); barcodes.push(b); } }));
    const seenT = new Set(); const blocks = [];
    exs.forEach((ex) => (ex.ocr_blocks || []).forEach((b) => { const t = compact(b.text); if (t && !seenT.has(t)) { seenT.add(t); blocks.push(b); } }));
    const warnings = [];
    exs.forEach((ex, i) => (ex.warnings || []).forEach((w) => warnings.push(`Image ${i + 1}: ${w}`)));
    return { ...exs[0], fields, unclear_fields: unclear, conflicts, barcodes, ocr_blocks: blocks, warnings };
  }

  window.ReadHints = { lines, unassigned, sterilization, storage, modelCandidate, merge };
})();
