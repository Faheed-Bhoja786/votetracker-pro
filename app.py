from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vote.db'
db = SQLAlchemy(app)

# Models
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100))
    music_on = db.Column(db.Boolean, default=False)
    election_status = db.Column(db.String(50), default='Upcoming')

class Party(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    voted = db.Column(db.Boolean, default=False)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer)
    party_id = db.Column(db.Integer)

# Routes
@app.before_first_request
def create_tables():
    db.create_all()
    if not Settings.query.first():
        settings = Settings(site_title="Vote Tracker")
        db.session.add(settings)
        db.session.commit()
    if not Admin.query.first():
        admin = Admin(username="admin", password="admin")
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def home():
    settings = Settings.query.first()
    parties = Party.query.all()
    return render_template('index.html', settings=settings, parties=parties)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/manage_voters', methods=['GET', 'POST'])
def manage_voters():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        voter = Voter(name=name)
        db.session.add(voter)
        db.session.commit()
    voters = Voter.query.all()
    return render_template('manage_voters.html', voters=voters)

@app.route('/manage_parties', methods=['GET', 'POST'])
def manage_parties():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        party = Party(name=name)
        db.session.add(party)
        db.session.commit()
    parties = Party.query.all()
    return render_template('manage_parties.html', parties=parties)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('admin'):
        return redirect(url_for('login'))
    settings = Settings.query.first()
    if request.method == 'POST':
        settings.site_title = request.form['site_title']
        settings.music_on = True if request.form.get('music_on') else False
        settings.election_status = request.form['election_status']
        db.session.commit()
    return render_template('settings.html', settings=settings)

# CORRECT VOTER LOGIN FLOW BASED ON YOUR ZIP
@app.route('/voter_login', methods=['GET', 'POST'])
def voter_login():
    if request.method == 'POST':
        name = request.form['name']
        id_number = request.form['id_number']

        if not id_number.isdigit() or not (7 <= len(id_number) <= 9):
            flash('ID number must be 7 to 9 digits.')
            return redirect(url_for('voter_login'))

        voter = Voter.query.filter_by(name=name).first()
        if not voter:
            voter = Voter(name=name)
            db.session.add(voter)
            db.session.commit()

        session['voter_id'] = voter.id
        return redirect(url_for('vote'))
    return render_template('voter_login.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    voter_id = session.get('voter_id')
    if not voter_id:
        return redirect(url_for('voter_login'))

    voter = Voter.query.get(voter_id)
    if voter.voted:
        flash("You have already voted.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        party_id = request.form['party_id']
        vote = Vote(voter_id=voter_id, party_id=party_id)
        voter.voted = True
        db.session.add(vote)
        db.session.commit()
        flash("Vote cast successfully!")
        return redirect(url_for('home'))

    parties = Party.query.all()
    return render_template('vote.html', parties=parties)

@app.route('/results')
def results():
    parties = Party.query.all()
    results = []
    for party in parties:
        count = Vote.query.filter_by(party_id=party.id).count()
        results.append({'party': party.name, 'votes': count})
    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
