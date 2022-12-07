from flask import Flask, render_template, flash, redirect, request, session, logging, url_for,current_app

from flask_sqlalchemy import SQLAlchemy

from forms import LoginForm, RegisterForm

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import jsonify

from google.cloud import storage
import google.oauth2.credentials as cred
import google.oauth2.service_account as service_account
from oauth2client.service_account import ServiceAccountCredentials
import os

app = Flask(__name__)

app_ctx = app.app_context()
app_ctx.push()

app.config['SECRET_KEY'] = '!9m@S-dThyIlW[pHQbN^'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@34.27.117.211/user_info'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name= db.Column(db.String(15), unique=True)

    username = db.Column(db.String(15), unique=True)

    email = db.Column(db.String(50), unique=True)

    password = db.Column(db.String(256), unique=True)

@app.route('/')
def home():
    image_list = []
    # Note: Client.list_blobs requires at least package version 1.17.0.
    credentials = service_account.Credentials.from_service_account_file('gcp-config.json')
    client = storage.Client(credentials=credentials, project='My First Project')
    
    bucket = client.list_blobs('bucket-cc-project-1')
    # blobs = storage_client.list_blobs(bucket_name)

    # Note: The call returns a response only when the iterator is consumed.
    for blob in bucket:
        image_list.append("https://storage.cloud.google.com/bucket-cc-project-1/"+ blob.name+"?authuser=1")
        print(blob.name)
    return render_template('index.html', img = image_list)

@app.route('/login/', methods = ['GET', 'POST'])
def login():

    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate:

        user = User.query.filter_by(email = form.email.data).first()

        if user:

            if check_password_hash(user.password, form.password.data):

                flash('You have successfully logged in.', "success")
                
                session['logged_in'] = True

                session['email'] = user.email 

                session['username'] = user.username

                return redirect(url_for('home'))

            else:

                flash('Username or Password Incorrect', "Danger")

                return redirect(url_for('login'))

    return render_template('login.html', form = form)


@app.route('/register/', methods = ['GET', 'POST'])
def register():
    
    form = RegisterForm(request.form)
    
    if request.method == 'POST' and form.validate():
    
        hashed_password = generate_password_hash(form.password.data, method='sha256')
    
        new_user = User(
            
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

    return redirect(url_for('home'))

@app.route('/upload/', methods=['POST'])
def upload():
    if request.method == 'POST':
        image_list = []
        projectpath = request.form['filepath']
        # credentials_dict = {
        #     'type': 'service_account',
        #     'client_id': '114115601628653603065',
        #     'client_email': '459278707338-compute@developer.gserviceaccount.com',
        #     'private_key_id': '12f42019861c323ddad08c5076f100d082cdbeb1',
        #     'private_key': '-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCpgacHKVWHXln2\nhMFrR2Aaj5S0qREpusWHmAPeU+Cppel16uIEMnPwWWEmVeDmtvLiKpdQfEcxM82y\ni2x0HkP5bsIxMAtjAIzPZOnT6oxayhtS1DsoZROplDtW7SZnWesCTqXOrcHNyY7p\nPL8/Q5HbP9qLkm37wcC95Ax9Q6AmHixfry59eyBCWo6LAcuOkhKI/UAPdJEOduMW\n3DYGccXrD7knZ/MXKMjIU+O6Arn3CeGcstpbBx+VSXQhKhC2/sVXQWcnMViiwvdc\nVdpDSEYPUmKXlxOW/5SdnZKPSIqAko1R8SiSYmFPwYSjwZjpDz5f3w5M/yV2EPAj\nRB0ukeJfAgMBAAECggEAFniJm/luzTNE2dlfisk7hEnkfM6s58tKxF7ypFaaQeMs\nv+UTcVr+4631ow9fcTZvnGvpA1J2XZ9wdWrmRb59ZGO6eqrT15wLDrNiDCXb1W1V\nkfVwojpEEQcFltB5dtoEvZmPgYanWpCN0X2sHMboXxhn8HjI+8cDtii1PyXn5SWD\nnxU5XEU+QhRSB8x3T+WVe9B/E71AD5MwtL0dXG4hSssQd0XD4DBdGjcOSjtHcrjy\ncNwH5F7nlpKE3fLzoTLN4cA3XCCuS9yUOCvK9tL9ZxzX6+u7PxL9cB4iVOu9NEUQ\nc1rV2U/qkQ6QWQvGwvdyfRdnweSlAj7zVnp9L45YAQKBgQDUBKJcP4PnQXgRGx1C\nPQxC1JuOzRWwz674F9yIOSDGdzKxqjzKK60ApgT7L13/7WkaFVywDlCZXZ1jekZ/\nqkffal7ag5At72v4ty2iz83BvCdynWkOYSt0CzUSZzl1M0ph+bc2l80cPuYHsXjK\nxlnEkBgs3nVDUgnNvciMLpXpHwKBgQDMq2iBlEh5YIObQMqh8PdF/6NgC1GQMQNQ\nIBCW5BQ/TrnPUSPCcE8SyJv58o2Tb+wPX07V5bxNApJE+DhhyCn10hFtKNB6AcCZ\nJHMV5pLocnQKl4m+LHOU7gA8pf6FCVNYWzGox/ewh2Uci58WTiKxTz/m0LUNyHLu\n2Q2cBNSewQKBgQCdvjTuXXNOA6/JSlsihTkyH+z8+ilBO8P6YgZ6c8am4ticxwQj\nhwtYiCz8leliGMkx1uL3Oi9NbBFFihwZsB95YjLgcTI8ev3iNqeFkwaLNepDpEod\noL4rwIrj/lkJkfetnZVq0NaSRVnwL2Knu5veWzchawHj7I3OvX0QjziKEQKBgQCn\n/+8ppjETSLDeqIFsCmK+14cgmEncJQ9GHvvfD9q62IFW9pB20z9k+Lxnn7yskEth\nluccVpaJVBoCeQm24dnniQZ65uyxqWyRiETbbkeafBBafWc4bj51uiMBpXPVegEq\n3rhVhcb/5TOPCeCNK5f4mUenzBtB9A67lflA3wo0QQKBgB31DEFDFil38LDHClwN\nS1mUAl6T9GfdqRynHCeS7jq9oruFzVwiQj5LVKpZc+aa0+Gu2SulleH5sLSGekRA\n6OKydS+k/fs+WBIwPpC13knpr1GBzCcPKwgoruNQhZPyziFGVN6NgFGhL1TmoVJy\nQuX0df6ubIbhJIJjigwhCzcd\n-----END PRIVATE KEY-----\n',
        # }
        # credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        #     credentials_dict
        # )
        # credentials = ServiceAccountCredentials.from_json_keyfile_name('gcp-config.json')
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
    
    app.run(host = '0.0.0.0')