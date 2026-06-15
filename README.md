# sd-webui-misc-scripts

Small extension containing various scripts to augment SD WebUI Forge.

## Scripts

- **ENQUEUE BUTTON** - Adds an **Enqueue** button next to the other generation buttons. When pressed it will snapshot the prompt and parameters to enqueue a generation job after the current job finishes. The button will show how many queued jobs are in queue.

- **UNLOAD MODELS** & **LIST MODELS** - injects two buttons to the bottom footer:
  - **List all models** (shown in the terminal)
  - **Unload models**

- **IMAGE DRAG & DROP** - Adds **drag-over (drag & drop)** handling so that when you drag a file over a tab button in the UI the tab will be opened (emulates a click on hover while dragging files). This makes it easier to drag an image onto the UI and drop it into the right tab, e.g. being in txt2img tab but wanting to drag an image into PNG Info.

- **TRANSPARENT BACKGROUND** - Adds a **Transparent Background** entry to the Extras tab allowing removal of background from images. The [Inspyrenet Rembg](https://github.com/plemeri/transparent-background) model will be downloaded on first use.

## SD WebUI Installation

1. Go into `Extensions` tab > `Install from URL`
2. Paste `https://github.com/otacoo/sd-webui-misc-scripts.git`
3. Press Install
4. Apply and Restart the UI

## Notes

- Only tested & working on [SD WebUI Forge Classic](https://github.com/Haoming02/sd-webui-forge-classic)

## License

[MIT](/LICENSE)

