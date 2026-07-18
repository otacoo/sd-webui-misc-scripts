from modules import script_callbacks, sd_models


def listModels():
    try:
        from backend import memory_management
    except ImportError:
        if hasattr(sd_models, 'list_loaded_weights'):
            sd_models.list_loaded_weights()
        else:
            print("\n(no model listing available)")
        return

    import torch

    from rich.console import Console
    from rich.table import Table

    table = Table(title="Currently Loaded Weights")
    table.add_column("Model", justify="left")
    table.add_column("VRAM", justify="right")
    table.add_column("Device", justify="right")

    mp_ids = set()

    for mdl in memory_management.current_loaded_models:
        try:
            mp = mdl.model
            name = mp.model.__class__.__name__
        except Exception:
            name = "Unknown"
            mp = None
        loaded = mdl.model_loaded_memory()
        vram = int(loaded / 2**20) if loaded > 0 else 0
        device = str(mdl.device) if loaded > 0 else "(offloaded)"
        mp_ids.add(id(mp))
        table.add_row(name, f"{vram} (MB)" if vram else "n.a.", device)

    sd_model = getattr(sd_models.model_data, 'sd_model', None)
    if sd_model is not None and sd_model.__class__.__name__ != 'FakeInitialModel':
        forge = getattr(sd_model, 'forge_objects', None)
        if forge is not None:
            for key in ('unet', 'vae', 'clip'):
                obj = getattr(forge, key, None)
                if obj is not None and id(obj) not in mp_ids:
                    try:
                        name = obj.model.__class__.__name__
                    except Exception:
                        name = key.upper()
                    loaded = obj.loaded_size()
                    vram = int(loaded / 2**20) if loaded > 0 else 0
                    try:
                        dev = str(obj.current_loaded_device()) if loaded > 0 else "(offloaded)"
                    except Exception:
                        dev = "?"
                    table.add_row(name, f"{vram} (MB)" if vram else "n.a.", dev)

    if torch.cuda.is_available():
        table.add_section()
        allocated = torch.cuda.memory_allocated() / (1024**2)
        free, total = torch.cuda.mem_get_info()
        table.add_row("CUDA Total", f"{total / (1024**2):.0f} MB", "")
        table.add_row("CUDA Used", f"{allocated:.0f} MB", "")
        table.add_row("CUDA Free", f"{free / (1024**2):.0f} MB", "")

    print("")
    Console().print(table)


def on_app_started(_demo, app):
    @app.post("/unload-models/unload")
    async def unload_models():
        try:
            sd_models.unload_model_weights()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @app.post("/unload-models/list")
    async def list_models():
        try:
            listModels()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


script_callbacks.on_app_started(on_app_started)
