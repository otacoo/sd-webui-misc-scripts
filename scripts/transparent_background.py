# This file implements Inspyrenet Rembg and Lucida transparent-background, both under MIT license
# Source: https://github.com/plemeri/transparent-background
# Source: https://github.com/egeorcun/lucida
#
# MIT License
#
# Copyright (c) 2022 Taehun Kim
# Copyright (c) 2026 egeorcun
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import time
import gradio as gr
from PIL import Image
from modules import scripts_postprocessing, shared

_remover = None
_lucida = None
_remover_error = None
_assign_patched = False

try:
    from transparent_background import Remover
except ModuleNotFoundError as e:
    _remover_error = e
    Remover = None


def _get_available_models():
    models = []
    if Remover is not None:
        models.append("Inspyrenet Rembg")
    try:
        import transformers
        models.append("Lucida")
    except ImportError:
        pass
    return models


def _load_lucida():
    global _lucida
    if _lucida is not None:
        return _lucida
    import torch
    from transformers import AutoModelForImageSegmentation
    device = "cuda" if torch.cuda.is_available() else "cpu"
    _lucida = AutoModelForImageSegmentation.from_pretrained(
        "egeorcun/lucida", trust_remote_code=True
    ).eval().to(device)
    return _lucida


def _lucida_process(image, threshold):
    import torch
    from torchvision import transforms

    model = _load_lucida()
    device = next(model.parameters()).device

    rgb = image.convert("RGB")
    orig_w, orig_h = rgb.size

    preprocess = transforms.Compose([
        transforms.Resize((1024, 1024)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    tensor = preprocess(rgb).unsqueeze(0).to(device)

    with torch.no_grad():
        out = model(tensor)[-1].sigmoid().cpu()[0, 0]

    out[out < threshold] = 0.0
    mask_pil = transforms.ToPILImage()(out).resize((orig_w, orig_h), Image.LANCZOS)
    mask = mask_pil.convert("L")
    return mask


def _patch_assign():
    global _assign_patched
    if _assign_patched:
        return
    orig = shared.state.__class__.assign_current_image

    def _patched(self, image):
        if image is not None and image.mode == "RGBA":
            bg = Image.new("RGB", image.size, (255, 255, 255))
            bg.paste(image, (0, 0), image)
            image = bg
        return orig(self, image)

    shared.state.__class__.assign_current_image = _patched
    _assign_patched = True


class ScriptPostprocessingTransparentBackground(scripts_postprocessing.ScriptPostprocessing):
    name = "Transparent Background"
    order = 10000

    def ui(self):
        models = _get_available_models()
        if not models:
            models = ["(none available)"]

        with gr.Accordion(label="Transparent Background", open=False):
            enabled = gr.Checkbox(label="Remove background", value=True)
            model_choice = gr.Radio(
                label="Model",
                choices=models,
                value=models[0] if models[0] != "(none available)" else None,
            )
            threshold = gr.Slider(
                label="Threshold",
                minimum=0.0,
                maximum=1.0,
                step=0.01,
                value=0.5,
            )
            output_mask = gr.Checkbox(
                label="Show mask as additional result", value=True
            )
        return {
            "enabled": enabled,
            "model": model_choice,
            "threshold": threshold,
            "output_mask": output_mask,
        }

    def process(self, pp, enabled, model, threshold, output_mask):
        if not enabled or not shared.opts.misc_enable_transparent_background:
            return

        if model == "Inspyrenet Rembg":
            if _remover_error is not None:
                print(
                    "Transparent Background: transparent_background module not found. "
                    "Run: python -m pip install transparent-background"
                )
                return

            global _remover
            if _remover is None:
                _patch_assign()
                _remover = Remover()

            rgb = pp.image.convert("RGB")
            mask = _remover.process(rgb, type="map", threshold=threshold).convert("L")

        elif model == "Lucida":
            _patch_assign()
            try:
                mask = _lucida_process(pp.image, threshold)
            except Exception as e:
                print(f"Transparent Background: Lucida failed — {e}")
                return

        else:
            return

        rgba = Image.merge("RGBA", (*pp.image.convert("RGB").split(), mask))

        ts = int(time.time())
        outpath = shared.opts.outdir_samples or shared.opts.outdir_extras_samples or os.path.join(shared.data_path, "outputs", "extras")
        os.makedirs(outpath, exist_ok=True)

        fmt = (shared.opts.samples_format or "png").lower()
        if fmt == "webp":
            rgba.save(os.path.join(outpath, f"transparent_{ts}.webp"), format="WEBP", lossless=True)
            print(f"Transparent Background: saved -> transparent_{ts}.webp")
            if output_mask:
                mask.save(os.path.join(outpath, f"mask_{ts}.webp"), format="WEBP", lossless=True)
                print(f"Transparent Background: saved -> mask_{ts}.webp")
        else:
            rgba.save(os.path.join(outpath, f"transparent_{ts}.png"), format="PNG")
            print(f"Transparent Background: saved -> transparent_{ts}.png")
            if output_mask:
                mask.save(os.path.join(outpath, f"mask_{ts}.png"), format="PNG")
                print(f"Transparent Background: saved -> mask_{ts}.png")

        pp.image = rgba

        if output_mask:
            pp.extra_images.append(mask.convert("RGB"))
