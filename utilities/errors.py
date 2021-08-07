class Error(Exception):
    """Base class for other exceptions"""
    pass


class InitErrors(Error):
    """For class of errors arising during initialisation"""
    pass


class ChromedriverMissing(InitErrors):
    """Raised when chromedriver is missing"""

    def __init__(self, file_path: str):
        self.chromedriver_path = file_path

    def __str__(self):
        return f"Please make sure chromedriver is at {self.chromedriver_path}"


class TempFolderNotEmpty(InitErrors):
    """Raised when temp folder is not empty"""

    def __init__(self, file_path: str):
        self.temp_path = file_path

    def __str__(self):
        return f"Please make sure temp folder is empty at {self.temp_path}.\n" \
               f"Temp folder will be deleted when program terminates."


class InputUrlInvalid(InitErrors):
    """Raised when input url is invalid"""
    pass


class NotUrlError(InputUrlInvalid):
    """Raised when the input is NOT a url"""

    def __init__(self, input_url: str):
        self.input_string = input_url

    def __str__(self):
        return f"Your input of {self.input_string} is not a URL."


class DomainMismatchError(InputUrlInvalid):
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


class PreDownloadError(Error):
    """
    Raised when error occurs pre-download
    Actually not an error if not trying to scale paywall, but why would you want to download then
    """
    pass


class CredentialsNotLoaded(PreDownloadError):
    """Raised when credentials not loaded"""
    pass


class NotSignedIn(PreDownloadError):
    """Raised when user tries to download without signing in"""
    pass
