# sd-webui-unload-models

Small extension containing various scripts to augment SD WebUI Forge.

## Scripts

- `scripts/unload_models.py` & `javascript/unload_models.js` - injects two buttons to the bottom footer:
  - **List all models** (shown in the terminal)
  - **Unload models**

- `javascript/drag_drop_tabs.js` - Adds drag-over (drag & drop) handling so that when you drag a file over a tab button in the UI the tab will be opened (emulates a click on hover while dragging files). This makes it easier to drag an image onto the UI and drop it into the right tab, e.g. being in txt2img tab but wanting to drag an image into PNG Info.

## SD WebUI Installation

1. Go into `Extensions` tab > `Install from URL`
2. Paste `https://github.com/otacoo/sd-webui-misc-scripts.git`
3. Press Install
4. Apply and Restart the UI

## Notes

- Tested & working on [SD WebUI Forge Classic](https://github.com/Haoming02/sd-webui-forge-classic)

## License

MIT

