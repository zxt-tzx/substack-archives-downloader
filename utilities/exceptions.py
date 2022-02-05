class InitialisationExceptions(Exception):
    """For exceptions arising during initialisation"""
    pass


class ChromedriverMissing(InitialisationExceptions):
    """Raised when chromedriver is missing"""

    def __init__(self, file_path: str):
        self.chromedriver_path = file_path

    def __str__(self):
        return f"Please make sure chromedriver is at {self.chromedriver_path}"


class TempFolderNotEmpty(InitialisationExceptions):
    """Raised when temp folder is not empty"""

    def __init__(self, file_path: str):
        self.temp_path = file_path

    def __str__(self):
        return f"Please make sure temp folder is empty at {self.temp_path}.\n" \
               f"Temp folder will be deleted when program terminates."


class InputUrlInvalid(InitialisationExceptions):
    """Raised when input url is invalid"""
    pass


class NotUrlException(InputUrlInvalid):
    """Raised when the input is NOT a url"""

    def __init__(self, input_url: str):
        self.input_string = input_url

    def __str__(self):
        return f"Your input of {self.input_string} is not a URL."


class DomainMismatchException(InputUrlInvalid):
    """Raised when the domain is not found in input url"""

    def __init__(self, input_url: str, domain: str):
        self.input_url = input_url
        self.domain_to_match = domain

    def __str__(self):
        return f"{self.domain_to_match} is not found in input {self.input_url}."


class DeformedSubdomain(InputUrlInvalid):
    """Raised when the input is NOT a url"""

    def __init__(self, input_url: str):
        self.input_url = input_url

    def __str__(self):
        return f"Please check the subdomain of your input {self.input_url}."


class LoginExceptions(Exception):
    """Raised when error arise while loading user credential and signing in"""
    pass


class CredentialsNotLoaded(LoginExceptions):  # not sure about this
    """Raised when trying to get credential before it is loaded"""
    pass


class UsernameNotEmail(LoginExceptions):
    """Username provided is not a valid email"""

    def __init__(self, input_email: str):
        self.input_email = input_email

    def __str__(self):
        return f"{self.input_email} is not an email address."


class ErrorWhileLoggingIn(LoginExceptions):
    """Raised when error encountered while logging in"""

    def __init__(self, when_error_occurred: str):
        self.when_error_occurred = when_error_occurred

    def __str__(self):
        return f"Something wrong happened after {self.when_error_occurred}."


class SubstackUrlNotSet(Exception):
    pass


class ErrorWhileLoadingArticles(Exception):
    def __init__(self, url_loaded: str):
        self.url_loaded = url_loaded

    def __str__(self):
        return f"Error while loading {self.url_loaded}."


class InitialLoadError(ErrorWhileLoadingArticles):
    pass


class SubsequentLoadError(ErrorWhileLoadingArticles):
    pass
# class PreDownloadExceptions(Exception):
#     """
#     Raised when exception occurs pre-download
#     Actually not an exception if not trying to scale paywall, but why would you want to download then
#     """
#     pass
#
#
# class ErrorWhileScrolling(PreDownloadExceptions):
#     """Raised if error encountered while scrolling"""
#     pass
#
#
# class ErrorWhileLoadingCache(PreDownloadExceptions):
#     """Raised if error encountered while loading articles into cache"""
#     pass
#
#
# class NotSignedIn(PreDownloadExceptions):
#     """Raised when user tries to download without signing in"""
#     pass
