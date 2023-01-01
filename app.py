from flask import Flask, render_template, flash, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from forms import LoginForm, RegisterForm
from werkzeug.security import check_password_hash, generate_password_hash
import google.oauth2.service_account as service_account
from google.cloud import storage

app = Flask(__name__)

app_context = app.app_context()
app_context.push()

app.config['SECRET_KEY'] = '!9m@S-dThyIlW[pHQbN^'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@34.27.117.211/user_info'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class UserDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(15), unique=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(256), unique=True)

@app.route('/')
def homepage():
    image_list = []
    credentials = service_account.Credentials.from_service_account_file('gcp-config.json')
    client = storage.Client(credentials=credentials, project='My First Project')
    
    bucket = client.list_blobs('bucket-cc-project-1')

    for blob in bucket:
        image_list.append("https://storage.cloud.google.com/bucket-cc-project-1/"+ blob.name+"?authuser=1")
        print(blob.name)
    return render_template('index.html', img = image_list)

@app.route('/login/', methods = ['GET', 'POST'])
def login():
    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate:
        user = UserDetails.query.filter_by(email = form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                flash('You have successfully logged in.', "success")
                session['logged_in'] = True
                session['email'] = user.email 
                session['username'] = user.username
                return redirect(url_for('homepage'))
            else:
                flash('Username or Password Incorrect', "Danger")
                return redirect(url_for('login'))

    return render_template('login.html', form = form)

@app.route('/register/', methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = UserDetails(
            name = form.name.data, 
            username = form.username.data, 
            email = form.email.data, 
            password = hashed_password)

        db.session.add(new_user)    
        db.session.commit()
    
        flash('You have successfully registered', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('register.html', form = form)

@app.route('/logout/')
def logout():
    session['logged_in'] = False
    return redirect(url_for('homepage'))

@app.route('/upload/', methods=['POST'])
def upload():
    if request.method == 'POST':
        image_list = []
        projectpath = request.form['filepath']
        
        credentials = service_account.Credentials.from_service_account_file('gcp-config.json')
        client = storage.Client(credentials=credentials, project='My First Project')
        
        bucket = client.bucket('bucket-cc-project-1')
        blob = bucket.blob(projectpath)
        blob.upload_from_filename("/Users/ravirajpurohit/Downloads/cc_project_pics/" + projectpath)
        bucket_1 = client.list_blobs('bucket-cc-project-1')
        for blob in bucket_1:
            image_list.append("https://storage.cloud.google.com/bucket-cc-project-1/"+ blob.name+"?authuser=1")
        return render_template('index.html', img = image_list)

if __name__ == '__main__':
    db.create_all()
    app.run(host = '0.0.0.0', port=8000)