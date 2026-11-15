"""Zero-shot check: ask a CLIP model which text description a candidate crop matches best.

No training on our pictograms: the candidate's ink crop is drawn black on white, padded to a square, and compared with
text prompts for the two pictograms and for common wrong symbols and clutter. The probability of a name is the softmax
share of its prompt among all prompts. Model: ``openai/clip-vit-base-patch32`` (about 600 MB, downloaded once from the
Hugging Face hub, CPU only, at most 4 threads).
"""

from __future__ import annotations

import os

import numpy as np

MODEL_ID = "openai/clip-vit-base-patch32"
PROMPTS = {
    "manufacturer": "a black and white pictogram of a factory with a chimney and a saw-tooth roof",
    "expiry": "a black and white pictogram of an hourglass",
    "caution": "a black and white warning triangle pictogram",
    "thermometer": "a black and white pictogram of a thermometer",
    "umbrella": "a black and white pictogram of an umbrella",
    "prohibition": "a black and white pictogram of a circle with a diagonal slash",
    "sun": "a black and white pictogram of a sun",
    "glass": "a black and white pictogram of a wine glass",
    "text": "a black and white picture of a letter or a number",
    "barcode": "a black and white picture of a barcode",
    "blob": "a black and white picture of a plain shape",
    "noise": "a black and white picture of noise or an empty page",
}
_STATE: dict = {}


def to_picture(ink: np.ndarray, side: int = 224):
    """Draw a 0/1 ink crop black on white, centred in a white square (aspect kept)."""
    from PIL import Image

    height, width = ink.shape
    scale = (side * 0.8) / max(height, width)
    new_w, new_h = max(1, round(width * scale)), max(1, round(height * scale))
    small = Image.fromarray(((1 - ink) * 255).astype(np.uint8)).resize((new_w, new_h), Image.Resampling.BILINEAR)
    canvas = Image.new("L", (side, side), 255)
    canvas.paste(small, ((side - new_w) // 2, (side - new_h) // 2))
    return canvas.convert("RGB")


def _load():
    """Load the model and processor once and cache the text embeddings of the prompts."""
    if not _STATE:
        import torch
        from transformers import CLIPModel, CLIPProcessor

        torch.set_num_threads(int(os.environ.get("SYMBOLS_TORCH_THREADS", "4")))
        model = CLIPModel.from_pretrained(MODEL_ID).eval()
        processor = CLIPProcessor.from_pretrained(MODEL_ID)
        with torch.no_grad():
            tokens = processor(text=list(PROMPTS.values()), return_tensors="pt", padding=True)
            text = model.get_text_features(**tokens)
            text = text if isinstance(text, torch.Tensor) else text.pooler_output
            text = text / text.norm(dim=-1, keepdim=True)
        _STATE.update(torch=torch, model=model, processor=processor, text=text)
    return _STATE


def probabilities(inks: list[np.ndarray]) -> np.ndarray:
    """Softmax over all prompts for each ink crop, shape (n, number of prompts)."""
    state = _load()
    torch = state["torch"]
    pictures = [to_picture(ink) for ink in inks]
    with torch.no_grad():
        pixels = state["processor"](images=pictures, return_tensors="pt")
        image = state["model"].get_image_features(**pixels)
        image = image if isinstance(image, torch.Tensor) else image.pooler_output
        image = image / image.norm(dim=-1, keepdim=True)
        logits = 100.0 * image @ state["text"].T
        return torch.softmax(logits, dim=1).numpy()


def clip_featurizer():
    """Featurizer for ``detector.featurize``: candidate crop to the probability of each pictogram prompt."""

    def featurizer(candidate, gray) -> dict[str, float]:
        probs = probabilities([candidate.ink])[0]
        names = list(PROMPTS)
        return {name: float(probs[names.index(name)]) for name in ("manufacturer", "expiry")}

    return featurizer
