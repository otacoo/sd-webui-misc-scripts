from modules import script_callbacks, sd_models


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
            sd_models.list_loaded_weights()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

script_callbacks.on_app_started(on_app_started)
