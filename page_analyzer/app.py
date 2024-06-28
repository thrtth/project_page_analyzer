import os
import psycopg2
from dotenv import load_dotenv
from flask import (Flask, render_template, request, flash,
                   redirect, url_for, get_flashed_messages)
import validators
from urllib.parse import urlparse, urlunparse
from datetime import datetime
import requests
from bs4 import BeautifulSoup


def normalize_url(url):
    parsed_url = urlparse(url)
    return urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))


def get_response(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response

    except Exception:
        flash('Произошла ошибка при проверке', 'danger')


def get_h1(html_page):
    h1_tag = html_page.find('h1')
    if h1_tag:
        return h1_tag.text.strip()
    else:
        return ''


def get_title(html_page):
    title_tag = html_page.find('title')
    if title_tag:
        return title_tag.text.strip()
    else:
        return ''


def get_meta(html_page):
    meta_tag = html_page.find('meta', attrs={'name': 'description'})
    if meta_tag:
        return meta_tag.get('content').strip()
    else:
        return ''


def get_db_conn():
    return psycopg2.connect(DATABASE_URL)


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

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
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute('SELECT '
                    'id '
                    'FROM urls '
                    'WHERE name = %s;',
                    (normalized_url,))
        url_exist = cur.fetchone()
        if url_exist:
            flash('Страница уже существует', 'info')
            conn.close()
            return redirect(url_for('get_url', url_id=url_exist[0]))
        else:
            cur.execute('INSERT INTO '
                        'urls (name, created_at) '
                        'VALUES (%s, %s) '
                        'RETURNING id;',
                        (normalized_url, datetime.now()))
            url_id = cur.fetchone()[0]
            conn.commit()
            conn.close()
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('get_url', url_id=url_id))


@app.route('/urls/<url_id>')
def get_url(url_id):
    messages = get_flashed_messages(with_categories=True)
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute('SELECT '
                    '* '
                    'FROM urls '
                    'WHERE id = %s;',
                    (url_id,))
        entry = cur.fetchone()
        url_data_dict = {
            'id': entry[0],
            'name': entry[1],
            'created_at': entry[2],
        }
        cur.execute('SELECT '
                    'url_checks.id, '
                    'url_checks.status_code, '
                    'url_checks.h1, '
                    'url_checks.title, '
                    'url_checks.description, '
                    'url_checks.created_at '
                    'FROM url_checks '
                    'JOIN urls '
                    'ON urls.id = url_id '
                    'WHERE urls.id = %s;',
                    (url_id,))
        checks = cur.fetchall()
        check_list = []
        for check in checks:
            check_dict = {
                'id': check[0],
                'status_code': check[1],
                'h1': check[2],
                'title': check[3],
                'meta': check[4],
                'created_at': check[5]
            }
            check_list.append(check_dict)
    conn.close()
    return render_template('url.html',
                           url=url_data_dict,
                           checks=check_list,
                           messages=messages)


@app.route('/urls', methods=['GET'])
def get_urls():
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute('SELECT '
                    'urls.id, '
                    'urls.name, '
                    'MAX(url_checks.created_at) '
                    'FROM urls LEFT JOIN url_checks '
                    'ON urls.id = url_checks.url_id '
                    'GROUP BY urls.id, urls.name '
                    'ORDER BY urls.created_at DESC;')

        urls = cur.fetchall()
        url_list = []
        for url in urls:
            cur.execute('SELECT '
                        'status_code '
                        'FROM url_checks '
                        'WHERE url_id = %s AND created_at = %s',
                        (url[0], url[2]))
            status = cur.fetchone()
            if status is not None:
                status = status[0]
            url_dict = {
                'id': url[0],
                'name': url[1],
                'latest_check': url[2],
                'status': status
            }
            url_list.append(url_dict)
    conn.close()
    return render_template('urls.html', urls=url_list)


@app.route('/urls/<url_id>/checks', methods=['POST'])
def url_checks(url_id):
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute('SELECT '
                    'name '
                    'FROM urls '
                    'WHERE id = %s', (url_id,))
        url_name = cur.fetchone()[0]
        response = get_response(url_name)
        if response is not None:
            status_code = response.status_code
            soup = BeautifulSoup(response.text, 'html.parser')
            h1 = get_h1(soup)
            title = get_title(soup)
            meta = get_meta(soup)
            cur.execute('INSERT INTO '
                        'url_checks '
                        '(url_id, '
                        'status_code, '
                        'h1, '
                        'title, '
                        'description, '
                        'created_at) '
                        'VALUES (%s, %s, %s, %s, %s, %s);',
                        (url_id, status_code, h1, title, meta, datetime.now()))
            conn.commit()
            flash('Страница успешно проверена', 'success')
    conn.close()
    return redirect(url_for('get_url', url_id=url_id))
