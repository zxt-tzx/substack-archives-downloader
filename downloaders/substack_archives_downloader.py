from datetime import datetime
import os
from typing import Union

import requests
from selenium.webdriver.common.by import By

from utilities import exceptions, helper
from downloaders.pdf_downloader import PDFDownloader

ArticlePostDate = int
ArticleTitle = str
ArticleUrl = str
ArticleTuple = tuple[ArticlePostDate, ArticleTitle, ArticleUrl]


class SubstackArchivesDownloader(PDFDownloader):
    element_selectors: dict[str, Union[str, tuple]] = {
        # elements used in sign-in
        'menu_button_css': '.menu-button > svg',
        'sign_in_button_css': '.premium',
        'go_to_login_link_text': 'Log in',
        'log_in_with_password_link_text': 'log in with password',
        'username_field_xpath': '//input[@name="email"]',
        'password_field_xpath': '//input[@name="password"]',
        'submit_button_xpath': '//button[@type="submit"]',
    }

    def __init__(self, input_url: str, is_headless: bool = False):
        helper.input_is_url(input_url)
        super().__init__(is_headless)
        self._url_cache = URLCache(input_url)
        self._user_credential = UserCredential()
        self._signed_in = False
        self.session = None

    # Methods for managing sign in
    def log_in(self, input_username: str, input_password: str):
        self._navigate_to_sign_in_page()  # TODO: we can navigate to sign in page without logging in
        self._load_credentials(input_username, input_password)
        self._log_in_using_browser()

    def download_k_most_recent(self, k: int):
        self._check_ready_to_download()
        self._load_k_articles_into_cache(k)
        article_tuples = self._url_cache.get_most_recent_k_article_tuples(k)
        self._convert_article_tuples_to_pdfs(article_tuples)

    def download_date_range(self, start_date: ArticlePostDate, end_date: ArticlePostDate):
        self._check_ready_to_download()
        assert start_date <= end_date
        self._load_articles_in_date_range(start_date, end_date)
        article_tuples = self._url_cache.get_article_tuples_by_date_range(start_date, end_date)
        self._convert_article_tuples_to_pdfs(article_tuples)

    def sign_out(self):
        # TODO
        """
        Usually, this is not needed as program simply terminates and kills the driver.
        But if we design Substack Archives Downloader to be "multi-use" instead of "single-use"...
        """
        return

    # Methods for logging in
    def _load_credentials(self, input_username: str, input_password: str):
        helper.input_email_validation(input_username)
        # TODO make sure input password meet some minimum criteria?
        self._user_credential.set_credential(input_username, input_password)

    def _navigate_to_sign_in_page(self):
        self._driver.get(self._url_cache.get_archive_url())
        menu_button = self._driver.find_element_by_css_selector(self.element_selectors['menu_button_css'])
        menu_button.click()
        sign_in_button = self._driver.find_element_by_css_selector(self.element_selectors['sign_in_button_css'])
        sign_in_url = sign_in_button.get_attribute('href')
        substack_subdomain = SubstackArchivesDownloader.extract_substack_subdomain(sign_in_url)
        self._url_cache.set_substack_url(substack_subdomain)
        self._driver.get(sign_in_url)

    def _log_in_using_browser(self):
        loaded_successfully = self._wait_for_element_to_load(By.LINK_TEXT,
                                                             self.element_selectors['log_in_with_password_link_text'])
        if not loaded_successfully:
            raise exceptions.ErrorWhileLoggingIn("clicking go_to_login_button")

        log_in_with_password_button = self._driver.find_element_by_link_text(
            self.element_selectors['log_in_with_password_link_text'])
        log_in_with_password_button.click()

        loaded_successfully = self._wait_for_element_to_load(By.XPATH, self.element_selectors['username_field_xpath'])
        if not loaded_successfully:
            raise exceptions.ErrorWhileLoggingIn("clicking log_in_with_password_button")

        username, password = self._user_credential.get_credential()
        username_field = self._driver.find_element_by_xpath(self.element_selectors['username_field_xpath'])
        username_field.send_keys(username)
        password_field = self._driver.find_element_by_xpath(self.element_selectors['password_field_xpath'])
        password_field.send_keys(password)
        submit_button = self._driver.find_element_by_xpath(self.element_selectors['submit_button_xpath'])
        submit_button.click()
        self._signed_in = True

    # Methods for downloading
    def _check_ready_to_download(self):
        if not self._user_credential.is_credential_filled():
            raise exceptions.CredentialsNotLoaded()
        # if not self._signed_in:
        #     raise exceptions.NotSignedIn()

    def _initialize_for_api_call(self):
        self.session = requests.Session()
        selenium_user_agent = self._driver.execute_script("return navigator.userAgent")
        self.session.headers.update({'User-Agent': selenium_user_agent})
        archive_api_url = self._url_cache.get_archive_api_url()
        response = self.session.get(
            f"{archive_api_url}?sort=new")
        if response.status_code != 200:
            raise exceptions.InitialLoadError(f"{archive_api_url}")

    """
    JSON shape:
    {
        'id': {int} 48162762,
        'title': {str} 'Title of Article',
        'post_date' : {str} '2021-10-12T14:52:58.738Z',
        'canonical_url' : {str} ''https://newsletter.domain.com/p/slug'
    }
    """

    def _load_k_articles_into_cache(self, k: int):
        self._initialize_for_api_call()
        set_of_articles_saved = set()
        reached_end_of_articles = False
        while True:
            num_articles_saved = len(set_of_articles_saved)
            get_request_url = f"{self._url_cache.get_archive_api_url()}?sort=new&offset={num_articles_saved}"
            response = self.session.get(f"{get_request_url}")
            if response.status_code != 200:
                raise exceptions.SubsequentLoadError(f"{get_request_url}")
            json_response = response.json()  # automatically converted to list of dict
            if len(json_response) == 0:
                break
            for json_dict in json_response:
                article_id = json_dict['id']
                if article_id in set_of_articles_saved:
                    reached_end_of_articles = True
                    continue
                post_date = json_dict['post_date']
                converted_date = SubstackArchivesDownloader.convert_json_date_to_yyyymmdd(post_date)
                title = json_dict['title']
                canonical_url = json_dict['canonical_url']
                self._url_cache.append_article_tuple(converted_date, title, canonical_url)
                set_of_articles_saved.add(article_id)
                num_articles_saved += 1
                if num_articles_saved == k:
                    return
            if len(set_of_articles_saved) >= k or reached_end_of_articles:
                break
            # TODO add random delay to make it more human-like?

    def _load_articles_in_date_range(self, start_date: int, end_date: int):
        self._initialize_for_api_call()
        num_articles_loaded = 0
        while True:
            get_request_url = f"{self._url_cache.get_archive_api_url()}?sort=new&offset={num_articles_loaded}"
            response = self.session.get(f"{get_request_url}")
            if response.status_code != 200:
                raise exceptions.SubsequentLoadError(f"{get_request_url}")
            json_response = response.json()  # automatically converted to list of dict
            if len(json_response) == 0:  # reached the end
                break
            num_articles_loaded += len(json_response)
            earliest_article_date = SubstackArchivesDownloader.convert_json_date_to_yyyymmdd(
                json_response[-1]['post_date'])
            if earliest_article_date > end_date:
                continue
            most_recent_article_date = SubstackArchivesDownloader.convert_json_date_to_yyyymmdd(
                json_response[0]['post_date'])
            if most_recent_article_date < start_date:
                break
            # if code reaches here, then we have articles in the date range
            for json_dict in json_response:
                post_date = json_dict['post_date']
                converted_date = SubstackArchivesDownloader.convert_json_date_to_yyyymmdd(post_date)
                if start_date <= converted_date <= end_date:
                    title = json_dict['title']
                    canonical_url = json_dict['canonical_url']
                    self._url_cache.append_article_tuple(converted_date, title, canonical_url)
            # TODO add random delay to make it more human-like?

    def _convert_article_tuples_to_pdfs(self, tuples: list[ArticleTuple]):
        for article_tuple in tuples:
            date, title, url = article_tuple
            filename_output = f'{date} {helper.clean_filename(title)}.pdf'
            filename_path_output = os.path.join(self._directory.output_path, filename_output)
            if os.path.isfile(filename_path_output):
                # skip URLs that have been previously downloaded
                # might lead to bugs if similar title + same publication date (quite unlikely)
                continue
            self._driver.get(url)
            self._save_current_page_as_pdf_in_output_folder(filename_path_output)

    @staticmethod
    def extract_substack_subdomain(sign_in_url: str):
        sub_domain_idx = sign_in_url.find('for_pub=') + len('for_pub=')
        # TODO a bit sloppy; might not work if for_pub= is not at the end of the url
        return sign_in_url[sub_domain_idx:]

    @staticmethod
    def convert_json_date_to_yyyymmdd(post_date: str) -> int:
        return int(datetime.strptime(post_date, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y%m%d'))


class URLCache:
    def __init__(self, validated_url: str):
        self._root_url = validated_url if validated_url[-1] != '/' else validated_url[:-1]
        self._archive_url = self._root_url + '/archive'
        self._article_tuples: list[ArticleTuple] = []
        self._substack_url = None

    # Getter for archive url
    def get_archive_url(self):
        return self._archive_url

    # Setter and getter for substack url and archive api url
    def set_substack_url(self, subdomain: str):
        self._substack_url = f"https://{subdomain}.substack.com"

    def get_substack_url(self):
        return self._substack_url

    def get_archive_api_url(self):
        if not self._substack_url:
            raise exceptions.SubstackUrlNotSet()
        return self._substack_url + '/api/v1/archive'

    # Setters and getters for article tuples
    # TODO a self-balancing tree would be more efficient O(log n) for managing article_tuples
    # for simplicity, we are just linear searching for everything  O(n) time (minimal difference for small n...)
    def append_article_tuple(self, date: ArticlePostDate, title: ArticleTitle, url: ArticleUrl):
        # for assumption that self.article_tuples_cache is sorted from ith to jth most recent
        # need to append article in reverse chronological order (technically can sort also...but meh)
        self._article_tuples.append((date, title, url))

    def get_cache_size(self) -> int:
        return len(self._article_tuples)

    def is_cache_empty(self) -> bool:
        return len(self._article_tuples) == 0

    def get_article_tuples_by_date(self, date: int) -> list[ArticleTuple]:
        output = []
        for article in self._article_tuples:
            article_date, _, _ = article
            if date == article_date:
                output.append(article)
        return output

    def get_article_tuples_by_date_range(self, start_date: ArticlePostDate,
                                         end_date: ArticlePostDate) -> list[ArticleTuple]:
        assert end_date >= start_date
        output = []
        # TODO: use binary search to find start_date faster?
        for article in self._article_tuples:
            article_date, _, _ = article
            if start_date <= article_date <= end_date:
                output.append(article)
        return output

    def get_article_tuple_by_idx(self, idx: int) -> ArticleTuple:
        return self._article_tuples[idx]

    def get_latest_article_tuple(self) -> ArticleTuple:
        return self._article_tuples[0]

    def get_earliest_article_tuple(self) -> ArticleTuple:
        # if self.get_cache_size() == 0:
        #     return None
        return self._article_tuples[-1]

    def get_most_recent_k_article_tuples(self, k: int) -> list[ArticleTuple]:
        # assumption: self.article_tuples_cache is sorted from ith to jth most recent
        assert k >= 1
        return self._article_tuples[:k]


class UserCredential:
    def __init__(self):
        self._username = ""
        self._password = ""
        self._is_credential_filled = False

    def get_credential(self) -> tuple[str, str]:
        if not self._is_credential_filled:
            raise exceptions.CredentialsNotLoaded()
        return self._username, self._password

    def set_credential(self, input_username: str, input_password: str):
        self._username = input_username
        self._password = input_password
        self._is_credential_filled = True

    def is_credential_filled(self):
        return self._is_credential_filled
