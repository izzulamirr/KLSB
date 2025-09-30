from app import create_app

app = create_app()

if __name__ == "__main__":
    # For development only; use a proper WSGI/ASGI server in production
    app.run(debug=True)
