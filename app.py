from flask import Flask, render_template, send_from_directory
from flask import jsonify
from course_scraper import run_scraper
from selenium.common.exceptions import WebDriverException
app = Flask(__name__)

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/scrape/<category>', methods=['POST'])
def scrape(category):
    try:
        result = run_scraper(category)
        return result
    except WebDriverException as e:
        return e.msg

@app.route('/results/<csv>')
def results(csv):
    return send_from_directory('results', str(csv))

if __name__ == '__main__':
    app.run(debug=True)




