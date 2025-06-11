from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///votetracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    voter_id = db.Column(db.String(20), unique=True)
    has_voted = db.Column(db.Boolean, default=False)

class Party(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    votes = db.Column(db.Integer, default=0)

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
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('dashboard.html')

@app.route('/manage_voters', methods=['GET', 'POST'])
def manage_voters():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form['name']
        voter_id = request.form['voter_id']
        voter = Voter(name=name, voter_id=voter_id)
        db.session.add(voter)
        db.session.commit()
        flash('Voter added successfully')
    voters = Voter.query.all()
    return render_template('manage_voters.html', voters=voters)

@app.route('/manage_parties', methods=['GET', 'POST'])
def manage_parties():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form['name']
        party = Party(name=name)
        db.session.add(party)
        db.session.commit()
        flash('Party added successfully')
    parties = Party.query.all()
    return render_template('manage_parties.html', parties=parties)

@app.route('/results')
def results():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    parties = Party.query.all()
    return render_template('results.html', parties=parties)

@app.route('/settings')
def settings():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('settings.html')

# Voter Side

@app.route('/voter_login', methods=['GET', 'POST'])
def voter_login():
    if request.method == 'POST':
        name = request.form['name']
        voter_id = request.form['voter_id']
        voter = Voter.query.filter_by(name=name, voter_id=voter_id).first()
        if voter:
            if voter.has_voted:
                flash("You have already voted.")
                return redirect(url_for('voter_login'))
            session['voter_id'] = voter.id
            return redirect(url_for('vote'))
        else:
            flash("Invalid voter credentials")
    return render_template('voter_login.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    voter_id = session.get('voter_id')
    if not voter_id:
        return redirect(url_for('voter_login'))
    voter = Voter.query.get(voter_id)
    parties = Party.query.all()

    if request.method == 'POST':
        party_id = request.form['party']
        party = Party.query.get(party_id)
        party.votes += 1
        voter.has_voted = True
        db.session.commit()
        session.pop('voter_id', None)
        flash("Thank you for voting!")
        return redirect(url_for('voter_login'))

    return render_template('vote.html', parties=parties)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# To create tables automatically
@app.before_first_request
def create_tables():
    db.create_all()
    # Create default admin if not exists
    if not Admin.query.first():
        default_admin = Admin(username='admin', password='admin')  # Change password later
        db.session.add(default_admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
