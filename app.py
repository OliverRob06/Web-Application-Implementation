from flask import Flask, render_template


app = Flask(__name__, template_folder = "html/template", static_folder = "static")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/info')
def info():
    return render_template('info.html')



if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0', port = 8000)