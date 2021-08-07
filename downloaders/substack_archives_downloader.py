from datetime import datetime
import os
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from utilities import errors, helper
from downloaders.pdf_downloader import PDFDownloader

ArticleDateNumeric = int
ArticleTitle = str
ArticleUrl = str
ArticleTuple = tuple[ArticleDateNumeric, ArticleTitle, ArticleUrl]


class SubstackArchivesDownloader(PDFDownloader):
    element_selectors: dict[str, str] = {
        # elements used in sign-in
        'menu_button_css': '.menu-button > svg',
        'go_to_login_link_text': 'Log in',
        'log_in_with_password_link_text': 'log in with password',
        'username_field_xpath': '//input[@name="email"]',
        'password_field_xpath': '//input[@name="password"]',
        'submit_button_xpath': '//button[@type="submit"]',
        # elements used on archives page
        'article_preview_xpath': '//*[@class="post-preview-content"]',
        'article_preview_date_bs_find_args': ("td", {"class": "post-meta-item post-date"}),
        'article_preview_title_bs_find_args': ("a", {"class": "post-preview-title newsletter"}),
        'article_preview_url_bs_find_args': ("a", {"class": "post-preview-title newsletter"}),
    }

    def __init__(self, input_url: str, is_headless: bool = False):
        validated_url = helper.input_url_validation(input_url)
        super().__init__(is_headless)
        self.credentials = self.Credentials()
        self.cache = self.Cache(validated_url)
        self.signed_in = False

    # Methods for managing sign in
    def load_credentials(self, input_username: str, input_password: str) -> bool:
        # TODO input validation to make sure username follows email format?
        # TODO make sure input password meet some minimum criteria?
        self.credentials.set_credentials(input_username, input_password)
        return True

    def sign_in(self) -> bool:
        # TODO avoid redundant sign-ins; track sign_in state?
        def sign_in_exit(success: bool) -> bool:
            self.signed_in = success
            return success

        self.driver.get(self.cache.archive_url)

        menu_button = self.driver.find_element_by_css_selector(self.element_selectors['menu_button_css'])
        menu_button.click()
        loaded_successfully = self.wait_for_element_to_load(By.LINK_TEXT,
                                                            self.element_selectors['go_to_login_link_text'])
        if not loaded_successfully:
            print("Something went wrong after clicking menu_button")  # TODO proper logging?
            return sign_in_exit(False)

        go_to_login_button = self.driver.find_element_by_link_text(self.element_selectors['go_to_login_link_text'])
        go_to_login_button.click()
        loaded_successfully = self.wait_for_element_to_load(By.LINK_TEXT,
                                                            self.element_selectors['log_in_with_password_link_text'])
        if not loaded_successfully:
            print("Something went wrong after clicking go_to_login_button")
            return sign_in_exit(False)

        log_in_with_password_button = self.driver.find_element_by_link_text(
            self.element_selectors['log_in_with_password_link_text'])
        log_in_with_password_button.click()
        loaded_successfully = self.wait_for_element_to_load(By.XPATH, self.element_selectors['username_field_xpath'])
        if not loaded_successfully:
            print("Something went wrong after clicking log_in_with_password_button")
            return sign_in_exit(False)

        username, password, credentials_loaded = self.credentials.get_credentials()
        if not credentials_loaded:
            print("Credentials not loaded")
            return sign_in_exit(False)

        username_field = self.driver.find_element_by_xpath(self.element_selectors['username_field_xpath'])
        username_field.send_keys(username)
        password_field = self.driver.find_element_by_xpath(self.element_selectors['password_field_xpath'])
        password_field.send_keys(password)
        submit_button = self.driver.find_element_by_xpath(self.element_selectors['submit_button_xpath'])
        submit_button.click()

        loaded_successfully = self.wait_for_element_to_load(By.XPATH, self.element_selectors['article_preview_xpath'])
        if not loaded_successfully:
            print("Something went wrong after submitting credentials")
        return sign_in_exit(loaded_successfully)

    def sign_out(self):
        # TODO
        return

    # Methods for scrolling down archives page
    def scroll_until_k_articles(self, k: int):
        self.driver.get(self.cache.archive_url)
        height_before_scrolling = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Scroll down to bottom
            time.sleep(self.wait_time.long_wait_time)  # TODO wait for JS async calls to finish; quite complex
            articles = self.driver.find_elements_by_xpath(self.element_selectors['article_preview_xpath'])
            height_after_scrolling = self.driver.execute_script("return document.body.scrollHeight")
            if height_after_scrolling == height_before_scrolling or len(articles) >= k:
                return  # stop scrolling if reach end of scroll OR predetermined no. of URLs attained
            height_before_scrolling = height_after_scrolling

    def scroll_until_date_reached(self, date: ArticleDateNumeric):
        self.driver.get(self.cache.archive_url)
        height_before_scrolling = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # Scroll down to bottom
            time.sleep(self.wait_time.long_wait_time)  # TODO replace with waiting for JS async calls to finish
            article_previews = self.driver.find_elements_by_xpath(self.element_selectors['article_preview_xpath'])
            height_after_scrolling = self.driver.execute_script("return document.body.scrollHeight")
            last_article_preview = article_previews[-1]
            article_html = last_article_preview.get_attribute('outerHTML')
            article_soup = BeautifulSoup(article_html, 'html.parser')
            raw_date = article_soup.find(*self.element_selectors['article_preview_date_bs_find_args']).text
            date_numeric = SubstackArchivesDownloader.process_raw_date_into_int(raw_date)
            if height_after_scrolling == height_before_scrolling or date > date_numeric:
                return  # strict inequality, in case multiple articles on same date

    """
    Assumptions for load_XXX functions: 
    - In between loads, there hasn't been new article published. TODO: Actually verify this (edge case, troublesome)
    - Articles are sorted from latest to earliest in cache
    If we switch data structures or expect the cache to persist, would need to tweak these functions accordingly 
    """

    # Methods for saving article-related info into cache
    def load_all_visible_articles_into_cache(self):
        article_previews = self.driver.find_elements_by_xpath(self.element_selectors['article_preview_xpath'])
        for article_preview in article_previews:
            article_html = article_preview.get_attribute('outerHTML')
            article_soup = BeautifulSoup(article_html, 'html.parser')
            raw_date = article_soup.find(*self.element_selectors['article_preview_date_bs_find_args']).text
            date_numeric = SubstackArchivesDownloader.process_raw_date_into_int(raw_date)
            title = article_soup.find(*self.element_selectors['article_preview_title_bs_find_args']).text
            url = article_soup.find(*self.element_selectors['article_preview_url_bs_find_args']).get('href')
            self.cache.append_article_tuple(date_numeric, title, url)

    def load_k_articles_into_cache(self, k: int):
        if self.cache.get_cache_size() >= k:
            return
        self.scroll_until_k_articles(k)
        self.load_all_visible_articles_into_cache()

    def load_all_articles_after_start_date(self, start_date: ArticleDateNumeric):
        if self.cache.get_cache_size() != 0:
            earliest_article_tuple = self.cache.get_earliest_article_tuple()
            earliest_article_date, _, _ = earliest_article_tuple
            if earliest_article_date < start_date:
                # all loaded alr, no need to reload again
                return
        self.scroll_until_date_reached(start_date)
        self.load_all_visible_articles_into_cache()

    # Methods for downloading
    def ready_to_download(self):
        if not self.credentials.filled_credentials:
            raise errors.CredentialsNotLoaded()
        if not self.signed_in:
            raise errors.NotSignedIn()

    def download_k_most_recent(self, k: int):
        self.ready_to_download()
        self.load_k_articles_into_cache(k)
        article_tuples = self.cache.get_most_recent_k_article_tuples(k)
        self.convert_article_tuples_to_pdfs(article_tuples)

    def download_date_range(self, start_date: ArticleDateNumeric, end_date: ArticleDateNumeric):
        self.ready_to_download()
        print("Ready to download")  # for testing purposes TODO comment out
        assert start_date <= end_date
        self.load_all_articles_after_start_date(start_date)
        print("Loaded successfully")  # for testing purposes TODO comment out
        article_tuples = self.cache.get_article_tuples_by_date_range(start_date, end_date)
        self.convert_article_tuples_to_pdfs(article_tuples)

    def convert_article_tuples_to_pdfs(self, tuples: list[ArticleTuple]):
        for article_tuple in tuples:
            date, title, url = article_tuple
            filename_output = f'{date} {helper.clean_filename(title)}.pdf'
            filename_path_output = os.path.join(self.directory.output_path, filename_output)
            if os.path.isfile(filename_path_output):
                # skip URLs that have been previously downloaded
                # might lead to bugs if similar title + same publication date (quite unlikely)
                continue
            self.driver.get(url)
            self.save_current_page_as_pdf_in_output_folder(filename_path_output)

    @staticmethod
    def process_raw_date_into_string(raw_date: str) -> str:
        """
        :param raw_date takes the following formats
        - if published today: "4 hr ago"
        - if published this year but not today: "Aug 1"
        - if published before this year: "Dec 18, 2020"
        :return the publication date in yyyymmdd
        """
        if "hr" in raw_date or "ago" in raw_date:
            return datetime.today().strftime('%Y%m%d')
        published_this_year = "," not in raw_date
        if published_this_year:
            yyyy = datetime.today().strftime('%Y')
        else:
            yyyy = raw_date[-4:]
            raw_date = raw_date[:-6]
        mmdd = datetime.strptime(raw_date, '%b %d').strftime('%m%d')
        return f'{yyyy}{mmdd}'

    @staticmethod
    def process_raw_date_into_int(raw_date: str) -> int:
        return int(SubstackArchivesDownloader.process_raw_date_into_string(raw_date))

    class Credentials:
        def __init__(self):
            self.username = ""
            self.password = ""
            self.filled_credentials = False

        def get_credentials(self) -> tuple[str, str, bool]:
            return self.username, self.password, self.filled_credentials

        def set_credentials(self, input_username: str, input_password: str):
            self.username = input_username
            self.password = input_password
            self.filled_credentials = True

    class Cache:
        def __init__(self, validated_url: str):
            self.root_url = validated_url
            self.archive_url = self.root_url + '/archive'
            self.article_tuples: list[ArticleTuple] = []

        # TODO a self-balancing tree would be more efficient O(log n) for managing article_tuples
        # for simplicity, we are just linear searching for everything  O(n) time (minimal difference for small n...)
        def append_article_tuple(self, date: ArticleDateNumeric, title: ArticleTitle, url: ArticleUrl):
            # for assumption that self.article_tuples_cache is sorted from ith to jth most recent
            # need to append article in reverse chronological order (technically can sort also...but meh)
            self.article_tuples.append((date, title, url))

        def get_cache_size(self) -> int:
            return len(self.article_tuples)

        def is_cache_empty(self) -> bool:
            return len(self.article_tuples) == 0

        def get_article_tuples_by_date(self, date: int) -> list[ArticleTuple]:
            output = []
            for article in self.article_tuples:
                article_date, _, _ = article
                if date == article_date:
                    output.append(article)
            return output

        def get_article_tuples_by_date_range(self, start_date: ArticleDateNumeric,
                                             end_date: ArticleDateNumeric) -> list[ArticleTuple]:
            assert end_date >= start_date
            output = []
            # TODO: use binary search to find start_date faster?
            for article in self.article_tuples:
                article_date, _, _ = article
                if start_date <= article_date <= end_date:
                    output.append(article)
            return output

        def get_article_tuple_by_idx(self, idx: int) -> ArticleTuple:
            return self.article_tuples[idx]

        def get_latest_article_tuple(self) -> ArticleTuple:
            return self.article_tuples[0]

        def get_earliest_article_tuple(self) -> ArticleTuple:
            # if self.get_cache_size() == 0:
            #     return None
            return self.article_tuples[-1]

        def get_most_recent_k_article_tuples(self, k: int) -> list[ArticleTuple]:
            # assumption: self.article_tuples_cache is sorted from ith to jth most recent
            assert k >= 1
            return self.article_tuples[:k]
