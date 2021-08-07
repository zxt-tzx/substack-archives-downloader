import re
from urllib.parse import urlparse

from validators.url import url

from utilities import exceptions


def input_url_validation(input_url: str, domain: str = None) -> str:
    """
    :param input_url: user-provided input that needs to be validated.
    No assumption about what form this might take and need to raise the correct exception accordingly
    :param domain: system-provided input of "domain.com" for verification to ensure correct site is scraped
    :return: a clean string of the form "https://subdomain.domain.com"
    """
    if not url(input_url, public=True):
        raise exceptions.NotUrlException(input_url)
    o = urlparse(input_url)
    network_location_string = o.netloc  # of the form "subdomain.domain.com"
    if domain not in network_location_string:
        raise exceptions.DomainMismatchException(input_url, domain)
    period_count = network_location_string.count('.')
    if period_count != 2:  # at least one period from domain checking; must have exactly 2 periods
        raise exceptions.DeformedSubdomain(input_url)
    subdomain = network_location_string.split('.')[0]
    if subdomain == 'www':
        # TODO: how to check if the input subdomain is valid? Need to fire up Selenium...(skip for now)
        raise exceptions.DeformedSubdomain(input_url)
    return f"https://{network_location_string}"


def clean_filename(input_string: str) -> str:
    """
    According to https://stackoverflow.com/a/31976060:
    illegal_chars_in_unix = ['/']
    illegal_chars_in_windows = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    :param input_string might have illegal chars that might not work as file names
    :return: cleaned string
    """
    pattern_to_filter = r'[<>"|?*\.]'  # filtering < > " | ? * .
    pattern_to_replace_with_underscore = r'[:/\\]'  # underscore : / \
    input_sans_illegal_chars = re.sub(pattern_to_replace_with_underscore, '_',
                                      re.sub(pattern_to_filter, '', input_string))
    return input_sans_illegal_chars.strip(" ")
