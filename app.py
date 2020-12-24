from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from werkzeug.utils import secure_filename
import sqlite3
from pathlib import Path
import pathlib
from hurry.filesize import alternative, size
from datetime import date

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = r'your directory\static\files'
app.config['auth_key'] = '123'
app.config['url'] = 'http://localhost:5000/'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/<token>', methods=['GET'])
def index(token):
    db = sqlite3.connect('data.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT image FROM main WHERE token = ?', (token,))
    result = cursor.fetchone()
    size2 = size(os.path.getsize(f'static/files/{result[0]}'), system=alternative)
    path = pathlib.Path(f'static/files/{result[0]}')
    upload_date = date.fromtimestamp(os.stat(f'static/files/{result[0]}').st_ctime)
    if result:
        return render_template('index.html', image='files/' + result[0], size=size2, name=token, type=path.suffix,
                               upload=upload_date)
    elif result is None:
        return render_template('404.html')
    cursor.close()
    db.close()


@app.route('/raw/<token>', methods=['GET'])
def raw(token):
    db = sqlite3.connect('data.sqlite')
    cursor = db.cursor()
    cursor.execute('SELECT image FROM main WHERE token = ?', (token,))
    result = cursor.fetchone()
    if result:
        return redirect(url_for('static', filename='files/' + result[0]), code=301)
    elif result is None:
        return render_template('404.html')
    cursor.close()
    db.close()


@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.form['key']
    if data == app.config['auth_key']:
        if 'file' not in request.files:
            resp = jsonify({'message': 'No file part in the request'})
            resp.status_code = 400
            return resp
        file = request.files['file']
        if file.filename == '':
            resp = jsonify({'message': 'No file selected for uploading'})
            resp.status_code = 400
            return resp
        if file and allowed_file(file.filename):
            db = sqlite3.connect('data.sqlite')
            cursor = db.cursor()

            p = Path(file.filename)
            p2 = str(p).replace("".join(p.suffixes), "")
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            sql = 'INSERT INTO main(token, image) VALUES(?,?)'
            val = (p2, filename)
            cursor.execute(sql, val)
            db.commit()
            cursor.close()
            db.close()

            resp = jsonify({'success': 'true', 'url': app.config['url'] + p2})
            resp.status_code = 201
            return resp
        else:
            resp = jsonify({'message': 'Allowed file types are png, jpg, jpeg, gif'})
            resp.status_code = 400
            return resp
    else:
        resp = jsonify({'message': 'Unauthorized'})
        resp.status_code = 400
        return resp

@app.errorhandler(404) 
def not_found(e): 
    return render_template("404.html") 

    
 
if __name__ == '__main__':
    app.run()
