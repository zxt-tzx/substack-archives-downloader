from downloaders.substack_archives_downloader import SubstackArchivesDownloader
from utilities import exceptions, helper


# TODO: allow user to indicate whether they want to use headless or normal browser
class SubstackArchivesDownloaderUserInterface:

    def __init__(self):
        self.downloader = None

    def get_substack_url(self) -> bool:
        while True:
            try:
                input_url = input("Enter the Substack URL you would like to scrape:\n")
                helper.input_url_validation(input_url, "substack.com")
                while True:
                    input_is_headless = input("Would you like to see the browser while it performs the scraping? \n"
                                              "Please type 'Y' or 'N'.\n")
                    if input_is_headless == 'Y' or input_is_headless == 'N':
                        break
                    else:
                        print("Please either type 'Y' or 'N'.")
                is_headless = input_is_headless == 'N'
                if is_headless:
                    print("The browser will perform the scraping in the background.")
                else:
                    print("A new window will open during the scraping.")
                self.downloader = SubstackArchivesDownloader(input_url, is_headless)
                return True
            except exceptions.InitialisationExceptions as init_exc:
                print(init_exc)
                print("Please fix the error above or try again later.\n")
            except Exception as exc:
                print(exc)
                print("Unexpected error occurred while initialising.")
                return False

    def get_user_credential(self) -> bool:
        while True:
            try:
                input_username = input("Please enter your Substack account email address:\n")
                helper.input_email_validation(input_username)
                input_password = input("Please enter your Substack account password:\n")
                # input_password = getpass(prompt="Please enter your Substack account password:\n")
                print("Please wait while we log in using the credential you provided...")
                self.downloader.log_in(input_username, input_password)
                print("Log in successful.")
                return True
            except exceptions.LoginExceptions as login_exc:
                print(login_exc)
                print("Please log in again or try again later.\n")
            except Exception as exc:
                print(exc)
                print("Unexpected error occurred while logging in.")
                self.downloader.shut_down()
                return False

    def get_user_download_choices(self) -> bool:
        while True:
            try:
                print("How would you like to download the articles?")
                print("To download articles falling within a date range, type '1'.")
                print("To download the most recent k articles, type '2'.")
                while True:
                    user_choice = input("Please enter your choice:\n")
                    if user_choice == "1" or user_choice == "2":
                        break
                    else:
                        print("Sorry, please either type '1' or '2'.\n")
                while True:
                    if user_choice == "1":
                        print("Please specify a date range using the format YYYYMMDD.")
                        date_range_start = input("Please enter the start date: \n")
                        date_range_end = input("Please enter the end date: \n")
                        if self.validate_start_date_and_end_date(date_range_start, date_range_end):
                            # TODO covert date_ranges into something more human readable?
                            print(f"Please wait while articles published between {date_range_start} "
                                  f"to {date_range_end} are being downloaded...")
                            self.downloader.download_date_range(int(date_range_start), int(date_range_end))
                            break
                        else:
                            print("Sorry, please enter a valid date range in the format YYYYMMDD.")
                    if user_choice == "2":
                        user_k = input("Please specify the number of most recent articles you'd like to download: \n")
                        if self.validate_k(user_k):
                            print(f"Please wait while the {user_k} most recently published articles "
                                  "are being downloaded...")
                            self.downloader.download_k_most_recent(int(user_k))
                            break
                        else:
                            print("Sorry please enter a valid integer k.")
                self.downloader.shut_down()
                return True
            except Exception as exc:
                print(exc)
                self.downloader.shut_down()
                return False

    @staticmethod
    def validate_k(k: str) -> bool:
        # TODO
        # check k is an integer
        # check k is a reasonable amount (and ask the user to confirm if k is too large?)
        return True

    @staticmethod
    def validate_start_date_and_end_date(date_range_start: str, date_range_end: str) -> bool:
        # TODO
        # check each conform to yyyymmdd format
        # check date_range_start <= date_range_end
        # check that they fall within some reasonable time range (check when was Substack founded o.o)
        return True

    @staticmethod
    def validate_yyyymmdd_format(input_string: str):
        # TODO
        return True
