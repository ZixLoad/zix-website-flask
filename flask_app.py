from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Remplacez par une clé secrète aléatoire et complexe
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modèle utilisateur
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    note = db.Column(db.Text, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
def homepage():
    """Affiche la page d'accueil et traite les formulaires soumis."""
    username = None
    available = None

    if request.method == 'POST':
        # Obtenir le pseudonyme soumis par l'utilisateur
        username = request.form.get('username')
        # Vérifier la disponibilité du pseudonyme
        available = check_username_availability(username)

    # Rendre le template avec les résultats de la vérification
    return render_template('index.html', username=username, available=available)

@app.route('/about')
def about():
    """Affiche la page 'About'."""
    return render_template('about.html')

@app.route('/vault', methods=['GET', 'POST'])
@login_required
def vault():
    """Affiche la page 'Vault' pour la gestion des notes."""
    if request.method == 'POST':
        note = request.form.get('note')
        current_user.note = note
        db.session.commit()
        flash('Note mise à jour!', 'success')
    return render_template('vault.html', note=current_user.note)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Affiche la page d'inscription et traite les formulaires."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Vérifiez si l'utilisateur existe déjà
        if User.query.filter_by(username=username).first():
            flash('Le nom d’utilisateur existe déjà.', 'danger')
            return redirect(url_for('register'))
        # Hachez le mot de passe avant de le stocker
        hashed_password = generate_password_hash(password, method='sha256')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Inscription réussie!', 'success')
        return redirect(url_for('vault'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Affiche la page de connexion et traite les formulaires."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        # Vérifiez si l'utilisateur existe et le mot de passe est correct
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Connexion réussie!', 'success')
            return redirect(url_for('vault'))
        flash('Échec de la connexion. Vérifiez votre nom d’utilisateur et/ou mot de passe.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Déconnecte l'utilisateur et le redirige vers la page de connexion."""
    logout_user()
    flash('Déconnexion réussie.', 'success')
    return redirect(url_for('login'))

def check_username_availability(username):
    """Vérifie la disponibilité du pseudonyme sur Minecraft."""
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return False  # Le pseudo est déjà pris
        elif response.status_code == 204:
            return True   # Le pseudo est disponible
        else:
            return None    # Erreur ou autre situation
    except requests.RequestException as e:
        # Gestion des erreurs de requêtes
        print(f"Request failed: {e}")
        return None

@app.route('/statslol', methods=['GET', 'POST'])
def statslol():
    """Affiche la page d'accueil et traite les formulaires soumis."""
    username = None
    region = None
    opgg_url = None

    if request.method == 'POST':
        # Obtenir le pseudonyme et la région soumis par l'utilisateur
        username = request.form.get('username')
        region = request.form.get('region')

        # Remplacer le # par un tiret -
        if username and region:
            username_cleaned = username.replace('#', '-').replace(' ', '')
            opgg_url = f"https://www.op.gg/summoners/{region}/{username_cleaned}"

    # Rendre le template avec l'URL OP.GG
    return render_template('stats.html', username=username, region=region, opgg_url=opgg_url)

@app.route('/home', methods=['GET', 'POST'])
def home():
 return render_template('home.html')

if __name__ == '__main__':
    db.create_all()  # Crée les tables de la base de données si elles n'existent pas déjà
    app.run(debug=True)
