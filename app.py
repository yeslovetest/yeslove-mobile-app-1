from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/community')
def community():
    return render_template('community.html')

@app.route('/get-educated')
def get_educated():
    return render_template('get_educated.html')

@app.route('/get-help')
def get_help():
    return render_template('get_help.html')

@app.route('/groups')
def groups():
    return render_template('groups.html')

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

if __name__ == '__main__':
    app.run(debug=True)
