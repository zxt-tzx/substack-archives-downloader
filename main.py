from utilities.logging_config import setup_logging, get_logger
from user_interface import SubstackArchivesDownloaderUserInterface as downloaderUI

# Initialize logging
setup_logging()
logger = get_logger("main")


def main() -> None:
    ui = downloaderUI()
    successful_initialisation = ui.get_substack_url()
    if not successful_initialisation:
        log_exit_failure()
        return

    successful_get_credential = ui.get_user_credential()
    if not successful_get_credential:
        log_exit_failure()
        return

    successful_log_in = ui.login_using_credential()
    if not successful_log_in:
        log_exit_failure()
        return

    successful_podcast_download_choice = ui.get_user_download_podcasts_choice()
    if not successful_podcast_download_choice:
        log_exit_failure()
        return

    successful_download = ui.get_user_download_choices()
    log_exit_success() if successful_download else log_exit_failure()


def log_exit_failure() -> None:
    logger.error("We're sorry, something has gone wrong.")


def log_exit_success() -> None:
    logger.info("Your article(s) have been downloaded. Thank you for using Substack Archives Downloader. Have a nice day!")


if __name__ == "__main__":
    main()
