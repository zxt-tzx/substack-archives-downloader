import re


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
