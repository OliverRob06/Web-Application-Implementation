from flask import Flask, render_template


app = Flask(__name__, template_folder = "html/template")


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/info')
def info():
    return render_template('info.html')



if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0.0', port = 8000)