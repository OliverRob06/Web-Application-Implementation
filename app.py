from flask import Flask, render_template, request, redirect, url_for, session
from auth import ADMIN_PASSWD, admin_required

app = Flask(__name__, template_folder = "html/template", static_folder = "static")

#cookie - if anyone is logged in
app.secret_key = 'logged'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    #admin login 
    if request.method == 'POST':
        user = request.form.get('Username')
        pw = request.form.get('Password')
        print(f"DEBUG: User typed '{user}' and Password '{pw}'")
        if pw == ADMIN_PASSWD:
            session['role'] = 'admin'
            session['user'] = user

        #need different home page for admins and users
            return redirect(url_for('home'))
        else:
            return 'Wrong Password', 403

    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/account')
def account():
    return render_template('account.html')


@app.route('/api/admin-only')
@admin_required
def admin_secret():
    return "If you see this, the String Comparison worked and you are an Admin!"

if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 8000)