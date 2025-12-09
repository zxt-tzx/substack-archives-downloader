import re
from urllib.parse import urlparse

from validators.url import url
from validators.email import email

from utilities import exceptions


def input_is_url(input_url: str) -> None:
    if not url(input_url, public=True):
        raise exceptions.NotUrlException(input_url)


def input_email_validation(input_email: str):
    if not email(input_email):
        raise exceptions.UsernameNotEmail(input_email)


def clean_filename(input_string: str, allow_dots: bool = False) -> str:
    """
    According to https://stackoverflow.com/a/31976060:
    illegal_chars_in_unix = ['/']
    illegal_chars_in_windows = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    :param input_string might have illegal chars that might not work as file names
    :param allow_dots: whether to allow dots in the filename (useful for domain names)
    :return: cleaned string
    """
    if allow_dots:
        pattern_to_filter = r'[<>"|?*]'
    else:
        pattern_to_filter = r'[<>"|?*\.]'  # filtering < > " | ? * .
        
    pattern_to_replace_with_underscore = r'[:/\\]'  # underscore : / \
    input_sans_illegal_chars = re.sub(pattern_to_replace_with_underscore, '_',
                                      re.sub(pattern_to_filter, '', input_string))
    return input_sans_illegal_chars.strip(" ")


# unused as Substack newsletters can now be hosted on any domain
# wonder if there is a way to check if the entered URL is indeed a Substack-hosted newsletter
def _input_url_contains_subdomain(input_url: str, primary_domain_to_match: str) -> str:
    """
    :param input_url: user-provided input that needs to be validated.
    No assumption about what form this might take and need to raise the correct exception accordingly
    :param primary_domain_to_match: system-provided input of "domain.com" for verification to ensure correct site is scraped
    :return: a clean string of the form "https://subdomain.domain.com"
    """
    o = urlparse(input_url)
    network_location_string = o.netloc  # of the form "subdomain.domain.com"
    if primary_domain_to_match not in network_location_string:
        raise exceptions.DomainMismatchException(input_url, primary_domain_to_match)
    period_count = network_location_string.count('.')
    if period_count != 2:  # at least one period from domain checking; must have exactly 2 periods
        raise exceptions.DeformedSubdomain(input_url)
    subdomain = network_location_string.split('.')[0]
    if subdomain == 'www':
        # TODO: how to check if the input subdomain is valid? Need to fire up Selenium...(skip for now)
        raise exceptions.DeformedSubdomain(input_url)
    return f"https://{network_location_string}"
