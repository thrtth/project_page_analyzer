import os
import psycopg2
from dotenv import load_dotenv
from flask import (Flask, render_template, request, flash,
                   redirect, url_for, get_flashed_messages)
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from page_analyzer.tools.url_tools import is_valid_url, normalize_url
from page_analyzer.db_queries import queries
from page_analyzer.tools.page_tools import get_meta, get_title, get_h1


def get_response(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response

    except Exception:
        flash('Произошла ошибка при проверке', 'danger')


def get_db_conn():
    return psycopg2.connect(DATABASE_URL)


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['POST'])
def add_url():
    url = request.form['url']
    if not is_valid_url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422

    normalized_url = normalize_url(url)
    conn = get_db_conn()
    with conn.cursor() as cur:
        url_exist = queries.select_id(cur, normalized_url)
        if url_exist:
            flash('Страница уже существует', 'info')
            conn.close()
            return redirect(url_for('get_url', url_id=url_exist[0]))
        else:
            url_id = queries.insert_url(cur, normalized_url)
            conn.commit()
            conn.close()
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('get_url', url_id=url_id))


@app.route('/urls/<url_id>')
def get_url(url_id):
    messages = get_flashed_messages(with_categories=True)
    conn = get_db_conn()
    with conn.cursor() as cur:
        entry = queries.select_url(cur, url_id)
        url_data_dict = {
            'id': entry[0],
            'name': entry[1],
            'created_at': entry[2],
        }
        checks = queries.select_checks(cur, url_id)
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
        urls = queries.select_last_checks(cur)
        url_list = []
        for url in urls:
            status = queries.select_status_code(cur, url)
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
        url_name = queries.select_name(cur, url_id)
        response = get_response(url_name)
        if response is not None:
            status_code = response.status_code
            soup = BeautifulSoup(response.text, 'html.parser')
            h1 = get_h1(soup)
            title = get_title(soup)
            meta = get_meta(soup)
            queries.insert_check(cur, url_id, status_code, h1, title, meta)
            conn.commit()
            flash('Страница успешно проверена', 'success')
    conn.close()
    return redirect(url_for('get_url', url_id=url_id))
