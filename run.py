from app import create_app, db

app = create_app(config_name="testing")
import os
with app.app_context():
    db.create_all()
    print("Tabelle create con successo.")

if __name__ == "__main__":
    app.run()
