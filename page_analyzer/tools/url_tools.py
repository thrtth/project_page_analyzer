from urllib.parse import urlparse, urlunparse
import validators


def normalize_url(url):
    parsed_url = urlparse(url)
    return urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))


def is_valid_url(url):
    return validators.url(url)
