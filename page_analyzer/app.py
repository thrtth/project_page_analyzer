import os
import psycopg2
from dotenv import load_dotenv
from flask import (Flask, render_template, request, flash,
                   redirect, url_for, get_flashed_messages)
import validators
from urllib.parse import urlparse, urlunparse
from datetime import datetime


def normalize_url(url):
    parsed_url = urlparse(url)
    return urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))


keepalive_kwargs = {
  "keepalives": 1,
  "keepalives_idle": 60,
  "keepalives_interval": 10,
  "keepalives_count": 5
}

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL, **keepalive_kwargs)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', messages=messages)


@app.route('/urls', methods=['POST'])
def add_url():
    url = request.form['url']
    if not validators.url(url):
        flash('Некорректный URL', 'danger')
        return redirect(url_for('index'))
    normalized_url = normalize_url(url)
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM urls WHERE name = %s;', (normalized_url,))
        url_exist = cur.fetchone()
        if url_exist:
            flash('Страница уже существует', 'info')
            return redirect(url_for('get_url', url_id=url_exist[0]))
        else:
            cur.execute('INSERT INTO urls (name, created_at)'
                        ' VALUES (%s, %s) RETURNING id;',
                        (normalized_url, datetime.now()))
            url_id = cur.fetchone()[0]
            conn.commit()
            return redirect(url_for('get_url', url_id=url_id))


@app.route('/urls/<url_id>')
def get_url(url_id):
    messages = get_flashed_messages(with_categories=True)
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM urls WHERE id = %s;', (url_id,))
        entry = cur.fetchone()
        url_data_dict = {
            'id': entry[0],
            'name': entry[1],
            'created_at': entry[2]
        }
    return render_template('url.html', url=url_data_dict, messages=messages)


@app.route('/urls', methods=['GET'])
def get_urls():
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM urls ORDER BY created_at DESC;')
        urls = cur.fetchall()
        url_list = []
        for url in urls:
            url_dict = {
                'id': url[0],
                'name': url[1],
                'created_at': url[2]
            }
            url_list.append(url_dict)

    return render_template('urls.html', urls=url_list)
