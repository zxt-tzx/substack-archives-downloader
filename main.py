from user_interface import SubstackArchivesDownloaderUserInterface as downloaderUI


def main():
    ui = downloaderUI()
    successful_initialisation = ui.get_substack_url()
    if not successful_initialisation:
        print("We're sorry that something has gone wrong.")
        return
    successful_log_in = ui.get_user_credential()
    if not successful_log_in:
        print("We're sorry that something has gone wrong.")
        return

    successful_download = ui.get_user_download_choices()
    if successful_download:
        print("Your article(s) have been downloaded. Thank you for using Substack Archives Downloader. Have a nice day!")
    else:
        print("We're sorry that something has gone wrong.")


if __name__ == "__main__":
    main()
