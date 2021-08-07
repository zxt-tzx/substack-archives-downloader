from datetime import datetime
import os
import random
import re


def generate_random_float_within_interval(average: float, interval: float) -> float:
    return random.uniform(average - interval, average + interval)


def input_url_validation(input_url: str, domain: str = None) -> str:
    # TODO
    #  1. process input_url to become exactly  "https://XXXX.domain.com" (get rid of backslash if necessary)
    #  2. if specify domain as "substack", raise an error if input_url is deformed (hmm)
    #  3. More complex: how to check if the input subdomain is valid? Need to fire up Selenium...
    # raise InputUrlInvalidError(f"Input url of {input_url} is invalid")
    return input_url


def input_domain_validation(domain: str) -> bool:
    # TODO check to make sure domain is a valid XXX.com or XXX.net?
    return True


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


def process_raw_date_into_string(raw_date: str) -> str:
    """
    :param raw_date takes the following formats
    - if published today: "4 hr ago"
    - if published this year but not today: "Aug 1"
    - if published before this year: "Dec 18, 2020"
    :return the publication date in yyyymmdd
    """
    if "hr" in raw_date or "ago" in raw_date:
        return datetime.today().strftime('%Y%m%d')
    published_this_year = "," not in raw_date
    if published_this_year:
        yyyy = datetime.today().strftime('%Y')
    else:
        yyyy = raw_date[-4:]
        raw_date = raw_date[:-6]
    mmdd = datetime.strptime(raw_date, '%b %d').strftime('%m%d')
    return f'{yyyy}{mmdd}'


def process_raw_date_into_int(raw_date: str) -> int:
    return int(process_raw_date_into_string(raw_date))


def ensure_folder_exists(path_to_folder: str):
    if not os.path.isdir(path_to_folder):
        os.mkdir(path_to_folder)


def validate_b64_string(b64_string: bytes):
    if b64_string[0:4] != b'%PDF':
        # TODO use more specific error?
        raise ValueError('Missing the PDF file signature')
