from backend import create_app
from backend.config import load_config


app = create_app()


if __name__ == "__main__":
    config = load_config()
    app.run(port=config.get("port", 8000), debug=False)
