from user_interface import SubstackArchivesDownloaderUserInterface as downloaderUI


def main() -> None:
    ui = downloaderUI()
    successful_initialisation = ui.get_substack_url()
    if not successful_initialisation:
        print_upon_exit_failure()
        return

    successful_get_credential = ui.get_user_credential()
    if not successful_get_credential:
        print_upon_exit_failure()
        return

    successful_log_in = ui.login_using_credential()
    if not successful_log_in:
        print_upon_exit_failure()
        return

    successful_podcast_download_choice = ui.get_user_download_podcasts_choice()
    if not successful_podcast_download_choice:
        print_upon_exit_failure()
        return

    successful_download = ui.get_user_download_choices()
    print_upon_exit_success() if successful_download else print_upon_exit_failure()


def print_upon_exit_failure() -> None:
    print("We're sorry, something has gone wrong.")


def print_upon_exit_success() -> None:
    print("Your article(s) have been downloaded. Thank you for using Substack Archives Downloader. Have a nice day!")


if __name__ == "__main__":
    main()
