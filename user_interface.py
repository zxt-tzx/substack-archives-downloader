import os
from dotenv import load_dotenv
from downloaders.substack_archives_downloader import SubstackArchivesDownloader
from utilities import exceptions, helper
from utilities.logging_config import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("ui")


class SubstackArchivesDownloaderUserInterface:

    def __init__(self):
        self.downloader = None
        self.username = None
        self.password = None
        self.download_podcasts = False

    def get_substack_url(self) -> bool:
        while True:
            try:
                # Try getting from environment variable first
                env_url = os.getenv('SUBSTACK_URL')
                if env_url:
                    input_url = env_url
                    logger.info(f"Using Substack URL from .env: {input_url}")
                else:
                    input_url = input("Enter the URL of the Substack-hosted newsletter you would like to scrape:\n")
                
                helper.input_is_url(input_url)
                
                # Try getting headless preference from environment variable
                env_headless = os.getenv('HEADLESS')
                if env_headless:
                    is_headless = env_headless.lower() == 'true'
                    logger.info(f"Using headless mode from .env: {is_headless}")
                else:
                    while True:
                        input_is_headless = input("Would you like to see the browser while it performs the scraping? \n"
                                                  "Please type 'Y' or 'N'.\n")
                        if input_is_headless == 'Y' or input_is_headless == 'N':
                            break
                        else:
                            print("Please type 'Y' or 'N'.")
                    is_headless = input_is_headless == 'N'

                if is_headless:
                    logger.info("The browser will perform the scraping in the background.")
                else:
                    logger.info("A new window will open during the scraping.")
                
                remove_comments = os.getenv('REMOVE_COMMENTS', 'false').lower() == 'true'
                if remove_comments:
                    logger.info("Comments section will be removed from PDFs.")
                    
                self.downloader = SubstackArchivesDownloader(input_url, is_headless, remove_comments)
                return True
            except exceptions.InitialisationExceptions as init_exc:
                logger.error(f"{init_exc}")
                logger.info("Please fix the error above or try again later.")
                if os.getenv('SUBSTACK_URL'):
                     return False
            except Exception as exc:
                logger.exception(f"Unexpected error occurred while initialising: {exc}")
                return False

    def get_user_credential(self) -> bool:
        while True:
            try:
                # Try getting from environment variables first
                env_email = os.getenv('SUBSTACK_EMAIL')
                env_password = os.getenv('SUBSTACK_PASSWORD')

                if env_email and env_password:
                    input_username = env_email
                    input_password = env_password
                    logger.info("Using credentials from .env file.")
                else:
                    input_username = input("Please enter your Substack account email address:\n")
                    helper.input_email_validation(input_username)
                    input_password = input("Please enter your Substack account password:\n")
                
                self.username = input_username
                self.password = input_password
                return True
            except exceptions.LoginExceptions as login_exc:
                logger.error(f"{login_exc}")
                logger.info("Please log in again or try again later.")
                if os.getenv('SUBSTACK_EMAIL'): 
                    return False
            except Exception as exc:
                logger.exception(f"Unexpected error occurred while getting credentials: {exc}")
                self.downloader.shut_down()
                return False

    def login_using_credential(self) -> bool:
        while True:
            try:
                logger.info("Please wait while we log in using the credential you provided...")
                self.downloader.log_in(self.username, self.password)
                logger.info("Log in successful.")
                return True
            except exceptions.LoginExceptions as login_exc:
                logger.error(f"{login_exc}")
                logger.info("Please log in again or try again later.")
                return False
            except Exception as exc:
                logger.exception(f"Unexpected error occurred while logging in: {exc}")
                self.downloader.shut_down()
                return False

    def get_user_download_podcasts_choice(self) -> bool:
        while True:
            try:
                # Try getting from environment variable
                env_podcasts = os.getenv('DOWNLOAD_PODCASTS')
                if env_podcasts:
                    self.download_podcasts = env_podcasts.lower() == 'true'
                    logger.info(f"Using podcast download preference from .env: {self.download_podcasts}")
                    return True

                while True:
                    input_is_download_podcasts = input("Would you like to download Podcast-type posts in addition to Newsletter-type posts? \n"
                                                       "Please type 'Y' or 'N'.\n")
                    if input_is_download_podcasts == 'Y' or input_is_download_podcasts == 'N':
                        break
                    else:
                        print("Please type 'Y' or 'N'.")
                self.download_podcasts = input_is_download_podcasts == 'Y'
                return True
            except Exception as exc:
                logger.exception(f"Unexpected error: {exc}")
                self.downloader.shut_down()
                return False

    # TODO decompose this method for easier debugging
    def get_user_download_choices(self) -> bool:
        while True:
            try:
                # Try getting from environment variables
                env_mode = os.getenv('DOWNLOAD_MODE')  # 'date' or 'count'
                
                if env_mode:
                    logger.info(f"Using download mode from .env: {env_mode}")
                    if env_mode == 'date':
                        date_range_start = os.getenv('DATE_RANGE_START')
                        date_range_end = os.getenv('DATE_RANGE_END')
                        if date_range_start and date_range_end:
                            logger.info(f"Using date range from .env: {date_range_start} to {date_range_end}")
                            if self.validate_start_date_and_end_date(date_range_start, date_range_end):
                                logger.info(f"Downloading articles published between {date_range_start} to {date_range_end}...")
                                self.downloader.download_date_range(int(date_range_start), int(date_range_end), bool(self.download_podcasts))
                                self.downloader.shut_down()
                                return True
                            else:
                                logger.error("Invalid date range in .env.")
                                return False
                        else:
                            logger.error("DATE_RANGE_START or DATE_RANGE_END missing in .env.")
                            return False
                    elif env_mode == 'count':
                        user_k = os.getenv('ARTICLE_COUNT')
                        if user_k:
                            logger.info(f"Using article count from .env: {user_k}")
                            if self.validate_k(user_k):
                                logger.info(f"Downloading the {user_k} most recently published articles...")
                                self.downloader.download_k_most_recent(int(user_k), bool(self.download_podcasts))
                                self.downloader.shut_down()
                                return True
                            else:
                                logger.error("Invalid ARTICLE_COUNT in .env.")
                                return False
                        else:
                            logger.error("ARTICLE_COUNT missing in .env.")
                            return False
                    else:
                        logger.error(f"Invalid DOWNLOAD_MODE in .env: {env_mode}. Use 'date' or 'count'.")
                        return False

                # Interactive mode if no env vars
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
                            logger.info(f"Downloading articles published between {date_range_start} to {date_range_end}...")
                            self.downloader.download_date_range(int(date_range_start), int(date_range_end), bool(self.download_podcasts))
                            break
                        else:
                            print("Sorry, please enter a valid date range in the format YYYYMMDD.")
                    elif user_choice == "2":
                        user_k = input("Please specify the number of most recent articles you'd like to download: \n")
                        if self.validate_k(user_k):
                            logger.info(f"Downloading the {user_k} most recently published articles...")
                            self.downloader.download_k_most_recent(int(user_k), bool(self.download_podcasts))
                            break
                        else:
                            print("Sorry please enter a valid integer k.")
                self.downloader.shut_down()
                return True
            except Exception as exc:
                logger.exception(f"Error during download: {exc}")
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
