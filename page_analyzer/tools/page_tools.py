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
