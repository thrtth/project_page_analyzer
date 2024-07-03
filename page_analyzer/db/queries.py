from datetime import datetime
from sqlalchemy import select, insert, func
from page_analyzer.db.models import Urls, UrlChecks


def select_id(session, url):
    req = select(Urls.id).where(Urls.name == url)
    return session.scalar(req)


def insert_url(session, url):
    req = (insert(Urls).values(name=url, created_at=datetime.now())
           .returning(Urls.id))
    url_id = session.execute(req).scalar()
    session.commit()
    return url_id


def select_url(session, url_id):
    req = select(Urls).where(Urls.id == url_id)
    return session.scalar(req)


def select_checks(session, url_id):
    req = select(UrlChecks).join(Urls).where(Urls.id == url_id)
    return session.scalars(req)


def select_last_checks(session):
    req = (select(Urls.id,
                  Urls.name,
                  func.max(UrlChecks.created_at).label('latest_check'))
           .join(UrlChecks, isouter=True)
           .group_by(Urls.id, Urls.name)
           .order_by(Urls.created_at.desc()))
    return session.execute(req)


def select_status_code(session, check):
    req = (select(UrlChecks.status_code)
           .where(UrlChecks.url_id == check.id)
           .where(UrlChecks.created_at == check.latest_check))
    return session.scalar(req)


def select_name(session, url_id):
    req = select(Urls.name).where(Urls.id == url_id)
    return session.scalar(req)


def insert_check(session, url_id, status_code, h1, title, meta):
    req = (insert(UrlChecks)
           .values(url_id=url_id,
                   status_code=status_code,
                   h1=h1,
                   title=title,
                   description=meta,
                   created_at=datetime.now()))
    session.execute(req)
    session.commit()
