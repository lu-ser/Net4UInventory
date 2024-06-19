from app import create_app, db
from app.models import User, Product, Location, Project, Loan

app = create_app()

with app.app_context():
    # Crea le tabelle nel database
    db.create_all()
    print("Tabelle create con successo.")
    db.init_app(app)
    # Inserisci dati di esempio se necessario
    if not User.query.first():
        user1 = User(username='admin', email='admin@example.com', password='admin123')
        db.session.add(user1)
        db.session.commit()
        print("Utente di esempio creato.")
    
    if not Location.query.first():
        location1 = Location(name='Laboratorio 1')
        db.session.add(location1)
        db.session.commit()
        print("Location di esempio creata.")
    
    if not Project.query.first():
        project1 = Project(name='Progetto di Ricerca', description='Descrizione del progetto')
        db.session.add(project1)
        db.session.commit()
        print("Progetto di esempio creato.")

if __name__ == "__main__":
    app.run(debug=True)
