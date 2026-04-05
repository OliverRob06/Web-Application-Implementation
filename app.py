from flask import Flask, render_template, request, redirect, url_for, session
from auth import ADMIN_PASSWD, admin_required
import os
from functools import wraps

app = Flask(__name__, template_folder = "html/template", static_folder = "static")

#cookie - if anyone is logged in 
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

#if the user isnt logged in send user to index.html
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    #admin login 
    if request.method == 'POST':
        user = request.form.get('Username')
        pw = request.form.get('Password')

        print(f"Login attempt for user: {user}")


        # currently to login as admin 
        # username = admin 
        # password = adminkey
        if user == 'admin' and pw == ADMIN_PASSWD:
            session['role'] = 'admin'
            session['user'] = user

        #need different home page for admins and users
            return redirect(url_for('home'))
        else:
            return 'Invalid Credentials', 403

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/account')
@login_required
def account():
    return render_template('account.html')


@app.route('/api/admin-only')
@admin_required
def admin_secret():
    return "If you see this, you are an Admin!"

if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 8000)