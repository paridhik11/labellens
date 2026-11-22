"""Live DailyMed lookup for the public medicine mode (CR-28).

A typed name that is not one of the curated products can still get a cited answer:

1. `search_labels` asks the DailyMed public API for human Rx and OTC labels with that name and returns a short
   candidate list (name, labeler, form). It never ranks a winner and never picks one.
2. The person picks a candidate. `LiveService.fetch` downloads that one label (zip with one SPL XML), parses it
   with the same section rules as the curated corpus (`scripts/real/build_medicine_corpus.py`), chunks it with the
   same chunker, builds the E5b retriever over its chunks and caches the parsed label on disk.
3. Answers come from the existing extractive pipeline over that one label's chunks. Every shown citation is checked
   against the chunk text (`unverified_sources`); a failure turns the answer into an abstention.

Every network call has a timeout and goes through one `Http` function, so tests pass recorded fixtures. Offline or an
API error raises `LiveUnavailable`; the API turns it into a plain message and the curated products stay usable.
Nothing here writes to the curated corpus (`data/medicine`).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from src.api.medicine import (
    BANNER,
    ReferenceProduct,
    candidate_json,
    derive_fields,
    reference_sections,
)
from src.common.schemas import Chunk
from src.crawl.chunk import compute_content_hash, split_text_into_chunks

BASE = "https://dailymed.nlm.nih.gov/dailymed/"
SEARCH_URL = BASE + "services/v2/spls.json"
LIVE_LABEL = "Fetched live from DailyMed, not in the curated set"
HUMAN_DOCTYPES = ("34390-5", "34391-3")  # OTC and prescription human labels (SPL document type codes)
SEARCH_TIMEOUT_S = 8.0
FETCH_TIMEOUT_S = 40.0
MAX_BYTES = 40_000_000
MAX_EXPANDED_BYTES = 200_000_000
LIST_LIMIT = 10  # candidates shown; the response says how many matched in all
NS = {"s": "urn:hl7-org:v3"}
SETID_RE = re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
LIVE_ID_RE = re.compile(r"^live_[0-9a-f]{16}_v\d{1,4}$")
HUMAN_SPL_CODES = {"34390-5", "34391-3"}
# Same section codes as scripts/real/build_medicine_corpus.CATEGORIES (a test keeps the two equal).
CATEGORIES = {
    "34067-9": "labelling", "34089-3": "labelling", "51945-4": "labelling",
    "34066-1": "warnings", "34070-3": "warnings", "34071-1": "warnings",
    "43685-7": "warnings", "34072-9": "warnings", "34076-0": "warnings",
    "50570-1": "warnings", "50569-3": "warnings", "50568-5": "warnings",
    "50567-7": "warnings", "50566-9": "warnings", "53414-9": "warnings",
    "50565-1": "warnings", "34068-7": "dosage",
}


class LiveUnavailable(Exception):
    """DailyMed could not be reached or answered badly. `reason` is offline, timeout or api_error."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(f"{reason}: {message}")
        self.reason, self.message = reason, message


class LiveFetchError(Exception):
    """A label was reached but cannot be used. `code` is a short machine code (not_a_human_label, no_text, ...)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code, self.message = code, message


Http = Callable[[str, float, int], bytes]  # (url, timeout seconds, max bytes) -> body


def default_http(url: str, timeout: float, max_bytes: int) -> bytes:
    """GET one URL with a timeout and a size cap. One retry on a timeout or a 5xx, none when offline."""
    if not url.startswith(BASE):
        raise LiveUnavailable("api_error", "only DailyMed addresses are fetched")
    request = Request(url, headers={"User-Agent": "LabelLens-public-medicine/1.0", "Accept": "application/json, */*"})
    for attempt in range(2):
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310 (https, host checked above)
                body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise LiveUnavailable("api_error", "DailyMed answered with more data than the size limit")
            return body
        except HTTPError as error:
            if error.code >= 500 and attempt == 0:
                time.sleep(1.0)
                continue
            raise LiveUnavailable("api_error", f"DailyMed answered HTTP {error.code}") from error
        except (TimeoutError, socket.timeout) as error:
            if attempt == 0:
                continue
            raise LiveUnavailable("timeout", "DailyMed did not answer in time") from error
        except URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                if attempt == 0:
                    continue
                raise LiveUnavailable("timeout", "DailyMed did not answer in time") from error
            raise LiveUnavailable("offline", "DailyMed cannot be reached from this computer") from error
        except OSError as error:
            raise LiveUnavailable("offline", "DailyMed cannot be reached from this computer") from error
    raise LiveUnavailable("api_error", "no answer")  # pragma: no cover


# ---------------------------------------------------------------- search

_TITLE_LABELER = re.compile(r"\s*\[([^\[\]]*)\]\s*$")


def parse_title(title: str) -> dict[str, str]:
    """Split a DailyMed list title 'NAME (GENERIC) FORM [LABELER]' into its parts. Missing parts are empty."""
    text = " ".join(title.split())
    labeler = ""
    found = _TITLE_LABELER.search(text)
    if found:
        labeler = found.group(1).strip()
        text = text[: found.start()].strip()
    name, generic, form = text, "", ""
    if text.endswith(")") or ") " in text:
        close = text.rfind(")")
        depth, open_at = 0, -1
        for i in range(close, -1, -1):  # the parenthesis that closes at `close`
            if text[i] == ")":
                depth += 1
            elif text[i] == "(":
                depth -= 1
                if depth == 0:
                    open_at = i
                    break
        if open_at > 0:
            name, generic, form = text[:open_at].strip(), text[open_at + 1:close].strip(), text[close + 1:].strip()
    return {"product_name": name, "generic_name": generic, "dosage_form": form.lower(), "labeler": labeler}


def label_url(setid: str, version: int | None = None) -> str:
    """The public DailyMed page of one label."""
    return BASE + f"drugInfo.cfm?setid={setid}" + (f"&version={version}" if version else "")


def search_labels(name: str, http: Http = default_http, today: date | None = None) -> dict[str, Any]:
    """The LiveSearchResult for a typed name. Raises LiveUnavailable when DailyMed cannot answer.

    Human Rx and OTC labels only (two requests, merged and de-duplicated by set id, taken alternately so both kinds
    show). The list is in DailyMed's own order: it is a list to choose from, not a ranking.
    """
    query = " ".join(name.split())[:200]
    per_type: list[list[dict[str, Any]]] = []
    total = 0
    for doctype in HUMAN_DOCTYPES:
        url = SEARCH_URL + "?" + urlencode({"drug_name": query, "doctype": doctype, "pagesize": LIST_LIMIT})
        try:
            payload = json.loads(http(url, SEARCH_TIMEOUT_S, 2_000_000))
            rows = payload["data"]
            total += int(payload["metadata"]["total_elements"])
        except (ValueError, KeyError, TypeError) as error:
            raise LiveUnavailable("api_error", "DailyMed answered in a form this page does not understand") from error
        per_type.append(rows)
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for i in range(max(len(r) for r in per_type) if per_type else 0):
        for rows in per_type:
            if i >= len(rows):
                continue
            row = rows[i]
            setid = str(row.get("setid", "")).lower()
            if not SETID_RE.match(setid) or setid in seen or not isinstance(row.get("spl_version"), int):
                continue
            seen.add(setid)
            parts = parse_title(str(row.get("title", "")))
            candidates.append({
                "setid": setid, "version": row["spl_version"], "title": " ".join(str(row.get("title", "")).split()),
                **{k: v for k, v in parts.items() if v}, "published_date": str(row.get("published_date", "")),
                "url": label_url(setid, row["spl_version"]),
            })
    candidates = candidates[:LIST_LIMIT]
    out: dict[str, Any] = {
        "outcome": "candidates" if candidates else "no_candidates", "query": query, "source": "DailyMed",
        "searched_on": (today or date.today()).isoformat(), "candidates": candidates, "total_matches": total,
    }
    if not candidates:
        out["message"] = (f"DailyMed has no human drug label with the name {query!r}. Check the spelling, or type the "
                          "brand or the active ingredient.")
    elif total > len(candidates):
        out["message"] = (f"{total} labels match. The first {len(candidates)} are listed. Type a more exact name "
                          "(with strength or form) to narrow the list.")
    return out


# ---------------------------------------------------------------- one label

@dataclass
class LiveLabel:
    """One fetched, parsed label. `chunks` use the same ids and section keys as the curated corpus."""

    product_id: str
    name: str
    setid: str
    version: int
    effective_date: str
    fetched: str
    xml_sha256: str
    url: str
    labeler: str
    active_ingredients: list[str]
    chunks: list[Chunk] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        """The cache file content."""
        return {**{k: v for k, v in self.__dict__.items() if k != "chunks"},
                "chunks": [c.model_dump() for c in self.chunks]}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "LiveLabel":
        """Read a cache file back; the chunk hashes are re-checked."""
        chunks = [Chunk(**c) for c in data["chunks"]]
        for chunk in chunks:
            if chunk.hash != compute_content_hash(chunk.text):
                raise ValueError("cached chunk text does not match its hash")
        return cls(**{**{k: v for k, v in data.items() if k != "chunks"}, "chunks": chunks})

    def live_info(self) -> dict[str, Any]:
        """The contract LiveLabelInfo: what must be shown next to every live answer."""
        return {"label": LIVE_LABEL, "setid": self.setid, "version": self.version,
                "effective_date": self.effective_date, "fetched_on": self.fetched, "source_url": self.url}


def product_id_for(setid: str, version: int) -> str:
    """Stable id of one fetched label version: live_<16 hex of the set id>_v<version>."""
    return f"live_{setid.replace('-', '')[:16]}_v{version}"


def _text(node: ET.Element | None) -> str:
    return " ".join(" ".join(node.itertext()).split()) if node is not None else ""


def read_spl_zip(payload: bytes) -> bytes:
    """The one SPL XML inside a DailyMed zip, with size and shape checks."""
    try:
        with ZipFile(BytesIO(payload)) as archive:
            infos = archive.infolist()
            if sum(info.file_size for info in infos) > MAX_EXPANDED_BYTES:
                raise LiveFetchError("bad_archive", "The label archive is larger than the size limit.")
            xmls = [info for info in infos if info.filename.lower().endswith(".xml")]
            if len(xmls) != 1:
                raise LiveFetchError("bad_archive", "The label archive does not hold exactly one SPL document.")
            return archive.read(xmls[0])
    except BadZipFile as error:
        raise LiveFetchError("bad_archive", "DailyMed did not return a readable label archive.") from error


def parse_label(xml: bytes, setid: str, version: int, fetched: str) -> LiveLabel:
    """Verify identity and read sections. Raises LiveFetchError for a label that cannot be used.

    Same rules as the curated build, relaxed in one way: a label needs at least one labelling or warnings
    section (the curated build also requires dosage text). The set id and version must be the ones asked for.
    """
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as error:
        raise LiveFetchError("bad_archive", "The label XML could not be read.") from error
    code, identity = root.find("s:code", NS), root.find("s:setId", NS)
    number, effective = root.find("s:versionNumber", NS), root.find("s:effectiveTime", NS)
    if code is None or code.get("code") not in HUMAN_SPL_CODES:
        raise LiveFetchError(
            "not_a_human_label", "This is not a human drug label (device or veterinary labels are not used).")
    if identity is None or identity.get("root", "").lower() != setid:
        raise LiveFetchError("id_mismatch", "DailyMed returned a label with a different set id than the one chosen.")
    if number is None or number.get("value") != str(version):
        raise LiveFetchError("id_mismatch", "DailyMed returned a different version than the one chosen.")
    raw_date = effective.get("value", "") if effective is not None else ""
    try:
        effective_date = date(int(raw_date[:4]), int(raw_date[4:6]), int(raw_date[6:8])).isoformat()
    except ValueError as error:
        raise LiveFetchError("bad_archive", "The label has no valid effective date.") from error
    names = [_text(n) for n in root.findall(".//s:manufacturedProduct/s:manufacturedProduct/s:name", NS)]
    names += [_text(n) for n in root.findall(".//s:manufacturedMedicine/s:name", NS)]
    distinct = list(dict.fromkeys(n for n in names if n))
    if not distinct:
        raise LiveFetchError("no_text", "The label does not name its product.")
    name = " / ".join(distinct[:3])
    org = root.find(".//s:author//s:representedOrganization/s:name", NS)
    actives = [_text(n) for n in root.findall(".//s:ingredient[@classCode='ACTIB']/s:ingredientSubstance/s:name", NS)]
    url = label_url(setid, version)
    chunks: list[Chunk] = []
    categories: set[str] = set()
    parents = {child: parent for parent in root.iter() for child in parent}
    for index, section in enumerate(root.findall(".//s:section", NS), 1):
        current, category = section, None
        while current is not None and category is None:
            section_code = current.find("s:code", NS)
            category = CATEGORIES.get(section_code.get("code")) if section_code is not None else None
            current = parents.get(current)
        body = section.find("s:text", NS)
        if category is None or body is None:
            continue
        text = _text(body)
        if len(text.split()) < 5:
            continue
        title_text = _text(section.find("s:title", NS)) or category
        code_node = section.find("s:code", NS)
        loinc = code_node.get("code", "unknown") if code_node is not None else "unknown"
        key = f"{category}/{loinc}/{index}"
        for n, piece in enumerate(split_text_into_chunks(text), 1):
            chunks.append(Chunk(chunk_id=f"dailymed_{setid}_v{version}_s{index}_c{n}", source="DailyMed", url=url,
                                title=f"{name}: {title_text}", section=key, text=piece, fetched=fetched,
                                hash=compute_content_hash(piece), module="medicine"))
        categories.add(category)
    if not categories & {"labelling", "warnings"}:
        raise LiveFetchError("no_text", "This label has no usable labelling or warnings text.")
    return LiveLabel(product_id=product_id_for(setid, version), name=name, setid=setid, version=version,
                     effective_date=effective_date, fetched=fetched, xml_sha256=hashlib.sha256(xml).hexdigest(),
                     url=url, labeler=_text(org), active_ingredients=list(dict.fromkeys(a for a in actives if a)),
                     chunks=chunks)


class LiveCatalog:
    """The slice of MedicineCatalog the section and candidate builders read, for one live label."""

    def __init__(self, label: LiveLabel) -> None:
        self.chunks = {c.chunk_id: c for c in label.chunks}
        product = ReferenceProduct(
            product_id=label.product_id, name=label.name, setid=label.setid, version=label.version,
            effective_date=label.effective_date, url=label.url, fetched=label.fetched,
            chunk_ids=[c.chunk_id for c in label.chunks])
        product.fields, product.evidence = derive_fields(label.chunks)
        if label.labeler:
            product.fields["manufacturer"] = label.labeler
            product.evidence["manufacturer"] = {
                "chunk_id": "", "quote": label.labeler, "role": "SPL labeler; physical manufacturer not established",
                "source_type": "spl_metadata"}
        if label.active_ingredients:
            product.fields["active_substance"] = ", ".join(label.active_ingredients[:3]).lower()
            product.evidence["active_substance"] = {
                "chunk_id": "", "quote": ", ".join(label.active_ingredients[:3]), "source_type": "spl_metadata"}
        self.products = {label.product_id: product}


def product_body(label: LiveLabel) -> dict[str, Any]:
    """The contract PublicMatchResult for a live label the person picked (outcome live_selected, CR-28)."""
    catalog = LiveCatalog(label)
    candidate = candidate_json(catalog, label.product_id, 1.0, label.name)  # type: ignore[arg-type]
    candidate.pop("match_confidence")  # nothing was ranked: the person chose the label
    candidate["read_from_photo"] = {}
    sections = reference_sections(catalog, label.product_id)  # type: ignore[arg-type]
    return {
        "banner": BANNER, "outcome": "live_selected", "candidates": [candidate],
        "summary": f"{label.name}: label fetched live from DailyMed set {label.setid} (not in the curated set).",
        "sources": sections["summary"][:1] or sections["ingredients"][:1],
        "sections": {k: sections[k] for k in ("summary", "ingredients", "warnings", "sources", "ingredients_note")},
        "live": label.live_info(),
    }


def unverified_sources(sources: list[dict[str, Any]], label: LiveLabel) -> list[str]:
    """Why shown citations cannot be trusted: a chunk that is not in this label, or a quote that is not verbatim."""
    by_id = {c.chunk_id: c for c in label.chunks}
    problems = []
    for src in sources:
        chunk = by_id.get(src.get("chunk_id", ""))
        quote = src.get("quote", "")
        if chunk is None:
            problems.append(f"{src.get('chunk_id')}: not a chunk of this label")
        elif not quote or quote not in chunk.text:
            problems.append(f"{chunk.chunk_id}: quote is not verbatim")
    return problems


# ---------------------------------------------------------------- service

class LiveService:
    """Search, fetch, cache and answer for live labels. Tests pass `http`, `cache_dir` and `retriever_factory`."""

    def __init__(self, http: Http | None = None, cache_dir: Path | None = None,
                 retriever_factory: Callable[[list[Chunk]], Any] | None = None, today: Callable[[], date] = date.today,
                 enabled: bool | None = None) -> None:
        self.http = http or default_http
        self.cache_dir = cache_dir or Path(os.environ.get("LABELLENS_LIVE_DIR", "data/api/live_dailymed"))
        self._factory = retriever_factory or _e5b_over
        self._today = today
        self._retrievers: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.Lock()
        self.enabled = enabled if enabled is not None else os.environ.get("LABELLENS_LIVE_DAILYMED", "1") != "0"

    # search
    def search(self, name: str) -> dict[str, Any]:
        """LiveSearchResult. When DailyMed cannot answer: outcome unavailable with a reason and a plain message."""
        if not self.enabled:
            return self._unavailable("disabled", "Live lookup is switched off on this server.", name)
        try:
            return search_labels(name, self.http, self._today())
        except LiveUnavailable as error:
            return self._unavailable(error.reason, error.message, name)

    def _unavailable(self, reason: str, message: str, name: str) -> dict[str, Any]:
        return {"outcome": "unavailable", "query": " ".join(name.split())[:200], "source": "DailyMed", "reason": reason,
                "candidates": [], "searched_on": self._today().isoformat(),
                "message": f"{message} The 30 curated medicines still work: type one of their names or scan its pack."}

    # cache
    def _path(self, product_id: str) -> Path:
        if not LIVE_ID_RE.match(product_id):
            raise LiveFetchError("not_found", "Unknown live product id.")
        return self.cache_dir / f"{product_id}.json"

    def knows(self, product_id: str | None) -> bool:
        """True when this id is a live label that is cached on disk."""
        if not product_id or not LIVE_ID_RE.match(product_id):
            return False
        return (self.cache_dir / f"{product_id}.json").exists()

    def load(self, product_id: str) -> LiveLabel:
        """The cached label (LiveFetchError not_found when absent or damaged)."""
        path = self._path(product_id)
        try:
            return LiveLabel.from_json(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise LiveFetchError(
                "not_found", "This live label is not in the cache. Search and pick it again.") from error

    def fetch(self, setid: str, version: int) -> LiveLabel:
        """Download (unless cached), parse, cache and index one picked label.

        Raises LiveUnavailable or LiveFetchError.
        """
        setid = setid.lower()
        if not SETID_RE.match(setid) or not 1 <= version <= 9999:
            raise LiveFetchError("bad_request", "Not a DailyMed set id and version.")
        product_id = product_id_for(setid, version)
        path = self._path(product_id)
        if path.exists():
            try:
                label = self.load(product_id)
            except LiveFetchError:
                label = None
            if label is not None:
                self.retriever(label)
                return label
        url = BASE + f"getFile.cfm?type=zip&setid={quote(setid)}&version={version}"
        xml = read_spl_zip(self.http(url, FETCH_TIMEOUT_S, MAX_BYTES))
        label = parse_label(xml, setid, version, self._today().isoformat())
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(label.to_json()), encoding="utf-8")
        tmp.replace(path)
        self.retriever(label)  # embeds the chunks now, so the first question is quick
        return label

    # answers
    def retriever(self, label: LiveLabel) -> Any:
        """The E5b retriever over this label's chunks only (kept for the last four labels)."""
        with self._lock:
            if label.product_id in self._retrievers:
                self._retrievers.move_to_end(label.product_id)
                return self._retrievers[label.product_id]
        built = self._factory(label.chunks)
        with self._lock:
            self._retrievers[label.product_id] = built
            while len(self._retrievers) > 4:
                self._retrievers.popitem(last=False)
        return built

    def ask(self, question: str, product_id: str, provider: Any, settings: Any) -> tuple[Any, LiveLabel]:
        """RagResult over one live label. Returns (result, label). Sources are label_section citations."""
        from src.rag.pipeline import answer_question

        label = self.load(product_id)
        chunks = {c.chunk_id: c for c in label.chunks}
        result = answer_question(question, "medicine", self.retriever(label), chunks, provider, settings, None)
        for source in result.sources:
            source["source_type"] = "label_section"
        return result, label

    def based_on(self, label: LiveLabel) -> str:
        """The `based_on` text of a live answer."""
        return (f"{LIVE_LABEL}. DailyMed set id {label.setid}, version {label.version}, effective "
                f"{label.effective_date}, fetched {label.fetched}; product {label.product_id}")

    def wire(self, result: Any, label: LiveLabel) -> dict[str, Any]:
        """The AnswerResponse body with the live label attached. Unverifiable citations become an abstention."""
        problems = unverified_sources(result.sources, label)
        if problems and result.outcome == "answered":
            result.outcome, result.cause, result.sources = "needs_human_check", "verification", []
        elif problems:
            result.sources = []
        body = result.to_wire(based_on=self.based_on(label))
        body["live"] = label.live_info()
        return body


def _e5b_over(chunks: list[Chunk]) -> Any:
    """The frozen E5b recipe (stemmed BM25 plus bge-large with the BGE prefix, RRF) over a small chunk list."""
    from src.ir.step18_config import e5b
    from src.ir.step18_systems import MODELS, Context18, sentence_model

    sentence_model(MODELS["large"]).to("cpu")  # same CPU pinning as the curated matcher
    return Context18(list(chunks)).build(e5b())
