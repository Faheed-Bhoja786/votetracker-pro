from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vote_tracker.db'
db = SQLAlchemy(app)

# MODELS
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    has_voted = db.Column(db.Boolean, default=False)

class Party(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    votes = db.Column(db.Integer, default=0)

# Initialize DB and create default admin on startup
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        default_admin = Admin(username='admin', password='admin')
        db.session.add(default_admin)
        db.session.commit()

# ADMIN ROUTES
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        admin = Admin.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if admin:
            session['admin'] = True
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))
    voters = Voter.query.all()
    parties = Party.query.all()
    return render_template('dashboard.html', voters=voters, parties=parties)

@app.route('/admin/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/admin/voters', methods=['GET', 'POST'])
def manage_voters():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        voter = Voter(voter_id=request.form['voter_id'], name=request.form['name'])
        db.session.add(voter)
        db.session.commit()
    voters = Voter.query.all()
    return render_template('manage_voters.html', voters=voters)

@app.route('/admin/parties', methods=['GET', 'POST'])
def manage_parties():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        party = Party(name=request.form['name'])
        db.session.add(party)
        db.session.commit()
    parties = Party.query.all()
    return render_template('manage_parties.html', parties=parties)

@app.route('/admin/results')
def results():
    if not session.get('admin'):
        return redirect(url_for('login'))
    parties = Party.query.all()
    return render_template('results.html', parties=parties)

# VOTER ROUTES
@app.route('/voter/login', methods=['GET', 'POST'])
def voter_login():
    if request.method == 'POST':
        voter = Voter.query.filter_by(voter_id=request.form['voter_id']).first()
        if voter:
            session['voter_id'] = voter.id
            return redirect(url_for('vote'))
    return render_template('voter_login.html')

@app.route('/voter/vote', methods=['GET', 'POST'])
def vote():
    voter = Voter.query.get(session.get('voter_id'))
    if not voter or voter.has_voted:
        return redirect(url_for('voter_login'))
    parties = Party.query.all()
    if request.method == 'POST':
        party = Party.query.get(int(request.form['party']))
        party.votes += 1
        voter.has_voted = True
        db.session.commit()
        return redirect(url_for('thank_you'))
    return render_template('vote.html', parties=parties)

@app.route('/voter/thank_you')
def thank_you():
    return "Thank you for voting!"

if __name__ == '__main__':
    app.run(debug=True)
