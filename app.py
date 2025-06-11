from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    voted = db.Column(db.Boolean, default=False)

class Party(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    logo = db.Column(db.String(200))

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer)
    party_id = db.Column(db.Integer)

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100))
    music_on = db.Column(db.Boolean, default=True)
    election_status = db.Column(db.String(50), default="Upcoming")

# Routes

@app.route('/')
def home():
    settings = SiteSetting.query.first()
    parties = Party.query.all()
    return render_template('index.html', settings=settings, parties=parties)

@app.route('/vote/<int:party_id>')
def vote(party_id):
    if session.get('voter_id'):
        voter_id = session['voter_id']
        voter = Voter.query.get(voter_id)
        if voter.voted:
            flash("You have already voted.")
            return redirect(url_for('home'))

        vote = Vote(voter_id=voter_id, party_id=party_id)
        voter.voted = True
        db.session.add(vote)
        db.session.commit()
        flash("Your vote has been recorded.")
        return redirect(url_for('home'))
    else:
        return redirect(url_for('voter_login'))

@app.route('/voter-login', methods=['GET', 'POST'])
def voter_login():
    if request.method == 'POST':
        name = request.form['name']
        voter = Voter.query.filter_by(name=name).first()
        if voter:
            session['voter_id'] = voter.id
            return redirect(url_for('home'))
        else:
            flash("Voter not found.")
    return render_template('voter_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session['admin_id'] = admin.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/manage-voters', methods=['GET', 'POST'])
def manage_voters():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        voter = Voter(name=name)
        db.session.add(voter)
        db.session.commit()
        flash('Voter added successfully.')

    voters = Voter.query.all()
    return render_template('manage_voters.html', voters=voters)

@app.route('/manage-parties', methods=['GET', 'POST'])
def manage_parties():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        party = Party(name=name)
        db.session.add(party)
        db.session.commit()
        flash('Party added successfully.')

    parties = Party.query.all()
    return render_template('manage_parties.html', parties=parties)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    settings = SiteSetting.query.first()
    if not settings:
        settings = SiteSetting(site_title="Vote Tracker", music_on=True, election_status="Upcoming")
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        settings.site_title = request.form['site_title']
        settings.music_on = bool(request.form.get('music_on'))
        settings.election_status = request.form['election_status']
        db.session.commit()
        flash("Settings updated.")

    return render_template('settings.html', settings=settings)

@app.route('/results')
def results():
    parties = Party.query.all()
    results = []
    for party in parties:
        count = Vote.query.filter_by(party_id=party.id).count()
        results.append({'party': party.name, 'votes': count})
    return render_template('results.html', results=results)

# TEMPORARY admin registration route (for first time only)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            return "Admin already exists!"

        new_admin = Admin(username=username, password=password)
        db.session.add(new_admin)
        db.session.commit()
        return "Admin registered successfully!"

    return '''
        <form method="post">
            Username: <input type="text" name="username"><br><br>
            Password: <input type="password" name="password"><br><br>
            <input type="submit" value="Register">
        </form>
    '''

# logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
