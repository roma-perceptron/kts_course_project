import os

from aiohttp.web import run_app
from kts_backend.web.app import setup_app


if __name__ == "__main__":
    run_app(
        setup_app(
            processor_count=3,
            config_path=os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "config.yml"
            )
        ),
        # host='165.227.133.221',
        port=8080
    )
