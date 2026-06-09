import gradio as gr
from modules import script_callbacks, shared


def on_ui_settings():
    section = ("misc_scripts", "Misc Scripts")

    shared.opts.add_option(
        "misc_enable_unload_models",
        shared.OptionInfo(
            True,
            "Enable 'Unload Models' buttons",
            gr.Checkbox,
            {"interactive": True},
            section=section,
        ).info("Adds buttons to unload models and list models in the footer."),
    )

    shared.opts.add_option(
        "misc_enable_drag_drop_tabs",
        shared.OptionInfo(
            True,
            "Enable drag-drop tab switching",
            gr.Checkbox,
            {"interactive": True},
            section=section,
        ).info("Auto-switches tabs when dragging files over them."),
    )

    shared.opts.add_option(
        "misc_enable_enqueue_prompt",
        shared.OptionInfo(
            True,
            "Enable Enqueue button",
            gr.Checkbox,
            {"interactive": True},
            section=section,
        ).info("Adds an Enqueue button during generation to queue prompts."),
    )

    shared.opts.add_option(
        "misc_enqueue_notifications",
        shared.OptionInfo(
            True,
            "Enqueue notifications",
            gr.Checkbox,
            {"interactive": True},
            section=section,
        ).info("Show a notification when queuing a prompt."),
    )

    shared.opts.add_option(
        "misc_enqueue_placement",
        shared.OptionInfo(
            "left",
            "Enqueue button placement",
            gr.Radio,
            {"choices": ["left", "middle", "right"], "interactive": True},
            section=section,
        ).info("Where to place the Enqueue button in the generate box."),
    )


script_callbacks.on_ui_settings(on_ui_settings)
