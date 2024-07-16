from datetime import datetime
from sqlalchemy import select, insert, func, null, or_

from page_analyzer.models.models import Urls, UrlChecks


def select_id(session, url):
    req = select(Urls.id).where(Urls.name == url)
    return session.scalar(req)


def insert_url(session, url):
    req = (insert(Urls).values(name=url, created_at=datetime.now())
           .returning(Urls.id))
    url_id = session.execute(req).scalar()
    return url_id


def select_url(session, url_id):
    req = select(Urls).where(Urls.id == url_id)
    return session.scalar(req)


def select_checks(session, url_id):
    req = select(UrlChecks).join(Urls).where(Urls.id == url_id)
    return session.scalars(req)


def select_last_checks(session):
    subq = (select(Urls.id,
                   Urls.name,
                   func.max(UrlChecks.created_at)
                   .label('latest_check'))
            .join(UrlChecks, isouter=True)
            .group_by(Urls.id, Urls.name)
            .order_by(Urls.created_at.desc())).cte('lc')

    req = (select(subq.c.id,
                  subq.c.name,
                  subq.c.latest_check,
                  UrlChecks.status_code)
           .join(UrlChecks, subq.c.id == UrlChecks.url_id, isouter=True)
           .where(or_(subq.c.latest_check == UrlChecks.created_at, subq.c.latest_check == null())))
    return session.execute(req)


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
