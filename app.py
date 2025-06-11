from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import random
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # change this to a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///votetracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    id_number = db.Column(db.String(9), nullable=False, unique=True)

class Party(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    votes = db.Column(db.Integer, default=0)

class ElectionStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)

# Initialize database tables
with app.app_context():
    db.create_all()

# Routes

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin'] = admin.username
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    voters = Voter.query.all()
    parties = Party.query.all()
    return render_template('admin_dashboard.html', voters=voters, parties=parties)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route('/voter/register', methods=['GET', 'POST'])
def voter_register():
    if request.method == 'POST':
        name = request.form['name']
        id_number = request.form['id_number']
        if len(id_number) < 7 or len(id_number) > 9:
            flash("ID Number must be between 7 and 9 digits")
            return render_template('voter_register.html')
        voter = Voter(name=name, id_number=id_number)
        try:
            db.session.add(voter)
            db.session.commit()
            flash("Registration successful")
            return redirect(url_for('home'))
        except:
            flash("ID Number already exists")
            db.session.rollback()
    return render_template('voter_register.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    status = ElectionStatus.query.first()
    if not status or status.status != "open":
        flash("Voting is currently closed")
        return redirect(url_for('home'))
    if request.method == 'POST':
        id_number = request.form['id_number']
        voter = Voter.query.filter_by(id_number=id_number).first()
        if voter:
            session['voter'] = voter.id
            return redirect(url_for('cast_vote'))
        else:
            flash("Voter not found")
    return render_template('voter_login.html')

@app.route('/cast_vote', methods=['GET', 'POST'])
def cast_vote():
    if 'voter' not in session:
        return redirect(url_for('vote'))
    parties = Party.query.all()
    if request.method == 'POST':
        party_id = request.form['party']
        party = Party.query.get(party_id)
        if party:
            party.votes += 1
            db.session.commit()
            session.pop('voter', None)
            flash("Vote cast successfully")
            return redirect(url_for('home'))
    return render_template('cast_vote.html', parties=parties)

@app.route('/admin/election_status', methods=['POST'])
def change_election_status():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    status = request.form['status']
    election_status = ElectionStatus.query.first()
    if not election_status:
        election_status = ElectionStatus(status=status)
        db.session.add(election_status)
    else:
        election_status.status = status
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_party', methods=['POST'])
def add_party():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    party_name = request.form['party_name']
    party = Party(name=party_name)
    db.session.add(party)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_admin', methods=['POST'])
def add_admin():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    username = request.form['username']
    password = request.form['password']
    admin = Admin(username=username, password=password)
    db.session.add(admin)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
