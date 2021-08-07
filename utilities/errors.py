class Error(Exception):
    """Base class for other exceptions"""
    pass


class InitErrors(Error):
    """For class of error arising during initialisation"""
    pass


class ChromedriverMissing(InitErrors):
    """Raised when chromedriver is missing"""
    pass


class TempFolderNotEmpty(InitErrors):
    """Raised when temp folder is not empty"""
    pass


class InputUrlInvalid(InitErrors):
    """Raised when input url is invalid"""
    pass


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
