import launch

if not launch.is_installed("transparent_background"):
    launch.run_pip(
        "install transparent-background>=1.3.4",
        "transparent-background",
    )
