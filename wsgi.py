from app import create_app

# Gunicorn entry point
app = create_app()

if __name__ == "__main__":
    app.run()
