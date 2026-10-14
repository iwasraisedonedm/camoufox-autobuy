"""Control-plane executable entry point."""

import uvicorn

from autobuy.settings import get_settings


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "autobuy.control_plane.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
    )


if __name__ == "__main__":
    run()
