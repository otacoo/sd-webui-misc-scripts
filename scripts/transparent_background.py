# This file implements transparent-background, MIT license
# Source: https://github.com/plemeri/transparent-background
#
# MIT License
#
# Copyright (c) 2022 Taehun Kim
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
_import_error = None
_assign_patched = False

try:
    from transparent_background import Remover
except ModuleNotFoundError as _e:
    _import_error = _e
    Remover = None


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
        with gr.Accordion(label="Transparent Background", open=False):
            enabled = gr.Checkbox(label="Remove background", value=True)
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
            "threshold": threshold,
            "output_mask": output_mask,
        }

    def process(self, pp, enabled, threshold, output_mask):
        if not enabled or not shared.opts.misc_enable_transparent_background:
            return

        if _import_error is not None:
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

        rgba = Image.merge("RGBA", (*rgb.split(), mask))

        fmt = (shared.opts.samples_format or "png").lower()
        if fmt == "webp":
            outpath = shared.opts.outdir_samples or shared.opts.outdir_extras_samples or os.path.join(shared.data_path, "outputs", "extras")
            os.makedirs(outpath, exist_ok=True)
            fn = f"transparent_{int(time.time())}.webp"
            rgba.save(os.path.join(outpath, fn), format="WEBP", lossless=True)
            print(f"Transparent Background: saved transparent WEBP -> {fn}")

        pp.image = rgba

        if output_mask:
            pp.extra_images.append(mask.convert("RGB"))
