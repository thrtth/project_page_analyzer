import os
from dotenv import load_dotenv
from flask import (Flask, render_template, request, flash,
                   redirect, url_for, get_flashed_messages)
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from page_analyzer.tools.url_tools import is_valid_url, normalize_url
from page_analyzer.db import queries
from page_analyzer.tools.page_tools import get_meta, get_title, get_h1


def get_response(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response

    except Exception:
        flash('Произошла ошибка при проверке', 'danger')


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)

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
    with Session(engine) as session:
        url_exist = queries.select_id(session, normalized_url)
        if url_exist:
            flash('Страница уже существует', 'info')
            return redirect(url_for('get_url', url_id=url_exist))
        else:
            url_id = queries.insert_url(session, normalized_url)
            session.commit()
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('get_url', url_id=url_id))


@app.route('/urls/<url_id>')
def get_url(url_id):
    messages = get_flashed_messages(with_categories=True)
    with Session(engine) as session:
        entry = queries.select_url(session, url_id)
        url_data_dict = {
            'id': entry.id,
            'name': entry.name,
            'created_at': entry.created_at,
        }
        checks = queries.select_checks(session, url_id)
        check_list = []
        for check in checks:
            check_dict = {
                'id': check.id,
                'status_code': check.status_code,
                'h1': check.h1,
                'title': check.title,
                'meta': check.description,
                'created_at': check.created_at
            }
            check_list.append(check_dict)
    return render_template('url.html',
                           url=url_data_dict,
                           checks=check_list,
                           messages=messages)


@app.route('/urls', methods=['GET'])
def get_urls():
    with Session(engine) as session:
        checks = queries.select_last_checks(session)
        url_list = []
        for check in checks:
            status = queries.select_status_code(session, check)
            url_dict = {
                'id': check.id,
                'name': check.name,
                'latest_check': check.latest_check,
                'status': status
            }
            url_list.append(url_dict)
    return render_template('urls.html', urls=url_list)


@app.route('/urls/<url_id>/checks', methods=['POST'])
def url_checks(url_id):
    with Session(engine) as session:
        url_name = queries.select_name(session, url_id)
        response = get_response(url_name)
        if response is not None:
            status_code = response.status_code
            soup = BeautifulSoup(response.text, 'html.parser')
            h1 = get_h1(soup)
            title = get_title(soup)
            meta = get_meta(soup)
            queries.insert_check(session, url_id, status_code, h1, title, meta)
            flash('Страница успешно проверена', 'success')
    return redirect(url_for('get_url', url_id=url_id))
