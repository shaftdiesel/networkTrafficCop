#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

from flask import Flask
from flask import render_template
app = Flask(__name__)


#@app.route("/hello")
@app.route("/chores")
def chores():
    return render_template("/Users/ssulliv1/workspace/choreChart/chores.html")
@app.route("/hello/<name>")
def hello(name=None):
  return render_template('index.html', name=name)

if __name__ == '__main__':
    app.run()
