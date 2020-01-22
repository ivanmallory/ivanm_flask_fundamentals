from flask import Flask, render_template, request
app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/result', methods=['POST'])
def results():
    name = request.form['name']
    location = request.form['dojo_location']
    language = request.form['language']
    textarea = request.form['comment']
    return render_template("result.html",name_on_template=name, location_on_template=location, language_on_template=language, comment_on_template=textarea)

if __name__ == "__main__":
    app.run(debug=True)

