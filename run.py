from backend import create_app

app = create_app()

if __name__ == '__main__':
    print("\n--- Starting Personalized Call Agent ---")
    app.run(debug=True)