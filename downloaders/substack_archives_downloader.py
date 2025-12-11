from datetime import datetime
import os
import time
from typing import Union

from urllib.parse import urlparse

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utilities import exceptions, helper
from utilities.logging_config import get_logger
from downloaders.pdf_downloader import PDFDownloader

logger = get_logger("substack")

ArticlePostDate = int
ArticleTitle = str
ArticleTags = str
ArticleUrl = str
ArticleTuple = tuple[ArticlePostDate, ArticleTitle, ArticleTags, ArticleUrl]


class SubstackArchivesDownloader(PDFDownloader):
    element_selectors: dict[str, Union[str, tuple]] = {
        # elements used in sign-in
        'get_to_sign_in_page_xpath': '//a[contains(text(), "Sign in")] | //button[contains(text(), "Sign in")]',
        'log_in_with_password_xpath': '//a[contains(., "password")]',
        'username_field_xpath': '//input[@name="email"]',
        'password_field_xpath': '//input[@name="password"]',
        'submit_button_xpath': '//button[@type="submit"]',
    }

    def __init__(self, input_url: str, is_headless: bool = False, remove_comments: bool = False):
        helper.input_is_url(input_url)
        super().__init__(is_headless)
        self.remove_comments = remove_comments
        self._url_cache = Cache(input_url)
        self._user_credential = UserCredential()
        self._signed_in = False
        self.session = None

    # Methods for managing sign in
    def log_in(self, input_username: str, input_password: str):
        self._driver.get(self._url_cache.get_archive_url())

        if self.load_cookies():
            self._driver.refresh()
            time.sleep(2)
            try:
                # Check if "Sign in" button is present with a short timeout
                WebDriverWait(self._driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, self.element_selectors['get_to_sign_in_page_xpath']))
                )
                logger.info("Cookies loaded but still not signed in. Proceeding with fresh login.")
            except TimeoutException:
                logger.info("Restored session from cookies.")
                self._signed_in = True
                return

        if self._is_headless:
            logger.warning("Running in headless mode without a saved session. "
                           "If a CAPTCHA appears, login will fail. "
                           "Please run without headless mode once to solve the CAPTCHA and save your session.")

        self._navigate_to_sign_in_page()
        self._load_credentials(input_username, input_password)
        self._log_in_using_browser()
        self.save_cookies()

    def download_k_most_recent(self, k: int, download_podcasts: bool = False):
        self._check_ready_to_download()
        self._load_k_articles_into_cache(k, download_podcasts)
        article_tuples = self._url_cache.get_most_recent_k_article_tuples(k)
        self._convert_article_tuples_to_pdfs(article_tuples)

    def download_date_range(self, start_date: ArticlePostDate, end_date: ArticlePostDate, download_podcasts: bool = False):
        logger.debug(f"Starting download_date_range({start_date}, {end_date}, {download_podcasts})")
        self._check_ready_to_download()
        assert start_date <= end_date
        self._load_articles_in_date_range(start_date, end_date, download_podcasts)
        article_tuples = self._url_cache.get_article_tuples_by_date_range(start_date, end_date)
        logger.info(f"Found {len(article_tuples)} articles to download")
        self._convert_article_tuples_to_pdfs(article_tuples)
        logger.debug("Finished converting to PDFs")

    def sign_out(self):
        """
        Usually, this is not needed as program simply terminates and kills the driver.
        But if we design Substack Archives Downloader to be "multi-use" instead of "single-use"...
        """
        return

    # Methods for logging in
    def _load_credentials(self, input_username: str, input_password: str):
        helper.input_email_validation(input_username)
        self._user_credential.set_credential(input_username, input_password)

    def _navigate_to_sign_in_page(self):
        self._driver.get(self._url_cache.get_archive_url())
        loaded_successfully = self._wait_for_element_to_load(By.XPATH, self.element_selectors['get_to_sign_in_page_xpath'])
        if not loaded_successfully:
            raise exceptions.ErrorWhileLoggingIn("finding sign in button")
            
        sign_in_button = self._driver.find_element(By.XPATH, self.element_selectors['get_to_sign_in_page_xpath'])
        sign_in_button.click()
        
        # Wait for potential redirect or modal
        time.sleep(1) 
        
        # Try to extract subdomain if possible, but don't fail if we can't
        try:
            sign_in_url = self._driver.current_url
            substack_subdomain = SubstackArchivesDownloader.extract_substack_subdomain(sign_in_url)
            self._url_cache.set_substack_url(substack_subdomain)
        except Exception:
            # If extraction fails (e.g. no for_pub in URL), we'll rely on root_url in Cache
            pass

    def _log_in_using_browser(self):
        loaded_successfully = self._wait_for_element_to_load(By.XPATH,
                                                             self.element_selectors['log_in_with_password_xpath'])
        if not loaded_successfully:
            # Maybe we are already on password screen? Check for password field
            if self._wait_for_element_to_load(By.XPATH, self.element_selectors['password_field_xpath']):
                 pass  # Proceed to enter credentials
            else:
                 raise exceptions.ErrorWhileLoggingIn("clicking log_in_with_password_button")
        else:
            log_in_with_password_button = self._driver.find_element(By.XPATH,
                self.element_selectors['log_in_with_password_xpath'])
            log_in_with_password_button.click()

        loaded_successfully = self._wait_for_element_to_load(By.XPATH, self.element_selectors['username_field_xpath'])
        if not loaded_successfully:
            raise exceptions.ErrorWhileLoggingIn("finding username field")

        username, password = self._user_credential.get_credential()
        username_field = self._driver.find_element(By.XPATH, self.element_selectors['username_field_xpath'])
        username_field.send_keys(username)
        
        # Wait for password field to be interactive
        self._wait_for_element_to_load(By.XPATH, self.element_selectors['password_field_xpath'])
        password_field = self._driver.find_element(By.XPATH, self.element_selectors['password_field_xpath'])
        password_field.send_keys(password)
        
        submit_button = self._driver.find_element(By.XPATH, self.element_selectors['submit_button_xpath'])
        submit_button.click()
        
        # Robust check for login success or failure
        # Reduced wait time, as we check for URL change dynamically anyway
        time.sleep(1)  
        
        current_url = self._driver.current_url
        
        # If we are still on the sign-in page, it might be due to CAPTCHA or MFA or wrong credentials.
        if "sign-in" in current_url:
            logger.info("Login not completed yet (possible CAPTCHA). Waiting for you to complete it in the browser...")
            
            # Reduced max retries to 30s (15 * 2s) which is reasonable for human interaction without blocking too long
            max_retries = 15
            for _ in range(max_retries):
                if "sign-in" not in self._driver.current_url:
                    break
                
                # Check for specific error messages to fail fast
                try:
                    error_element = self._driver.find_element(By.CSS_SELECTOR, ".error-message, .form-error")
                    if error_element and error_element.is_displayed():
                         raise exceptions.LoginExceptions(f"Login failed: {error_element.text}")
                except exceptions.LoginExceptions:
                    raise
                except:
                    pass
                    
                time.sleep(2)
            
            if "sign-in" in self._driver.current_url:
                 logger.warning("Still on sign-in page after waiting. Proceeding, but download might fail.")

        self._signed_in = True

    # Methods for downloading
    def _check_ready_to_download(self):
        if not self._user_credential.is_credential_filled():
            raise exceptions.CredentialsNotLoaded()

    def _initialize_for_api_call(self):
        logger.debug("Initializing API session...")
        self.session = requests.Session()
        selenium_user_agent = self._driver.execute_script("return navigator.userAgent")
        self.session.headers.update({'User-Agent': selenium_user_agent})
        
        # Copy cookies from selenium driver to requests session
        cookies = self._driver.get_cookies()
        logger.debug(f"Found {len(cookies)} cookies")
        for cookie in cookies:
            self.session.cookies.set(cookie['name'], cookie['value'])
            
        archive_api_url = self._url_cache.get_archive_api_url()
        logger.debug(f"Making API request to {archive_api_url}?sort=new")
        response = self.session.get(f"{archive_api_url}?sort=new")
        if response.status_code != 200:
            logger.error(f"API request failed! Response: {response.text[:500]}")
            raise exceptions.InitialLoadError(f"{archive_api_url} (Status: {response.status_code})")
        logger.debug("API initialization successful")

    def _load_k_articles_into_cache(self, k: int, download_podcasts: bool):
        self._initialize_for_api_call()
        set_of_articles_saved = set()
        reached_end_of_articles = False
        while True:
            num_articles_saved = len(set_of_articles_saved)
            get_request_url = f"{self._url_cache.get_archive_api_url()}?sort=new&offset={num_articles_saved}"
            response = self.session.get(f"{get_request_url}")
            if response.status_code != 200:
                raise exceptions.SubsequentLoadError(f"{get_request_url}")
            json_response = response.json()
            if len(json_response) == 0:
                break
            for json_dict in json_response:
                if json_dict['type'] == "podcast" and not download_podcasts:
                    continue
                article_id = json_dict['id']
                if article_id in set_of_articles_saved:
                    reached_end_of_articles = True
                    continue
                post_date = json_dict['post_date']
                converted_date = SubstackArchivesDownloader.convert_json_date_to_yyyymmdd(post_date)
                title = json_dict['title']
                tags = []
                for tag in json_dict['postTags']:
                    tags.append(tag['slug'])                    
                converted_tags = SubstackArchivesDownloader.convert_tags_to_string(tags)
                canonical_url = json_dict['canonical_url']
                self._url_cache.append_article_tuple(converted_date, title, converted_tags, canonical_url)
                set_of_articles_saved.add(article_id)
                num_articles_saved += 1
                if num_articles_saved == k:
                    return
            if len(set_of_articles_saved) >= k or reached_end_of_articles:
                break

    def _load_articles_in_date_range(self, start_date: int, end_date: int, download_podcasts: bool):
        logger.debug("Loading articles in date range")
        self._initialize_for_api_call()
        num_articles_loaded = 0
        while True:
            get_request_url = f"{self._url_cache.get_archive_api_url()}?sort=new&offset={num_articles_loaded}"
            response = self.session.get(f"{get_request_url}")
            if response.status_code != 200:
                raise exceptions.SubsequentLoadError(f"{get_request_url}")
            json_response = response.json()
            if len(json_response) == 0:
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
                if json_dict['type'] == "podcast" and not download_podcasts:
                    continue
                post_date = json_dict['post_date']
                converted_date = SubstackArchivesDownloader.convert_json_date_to_yyyymmdd(post_date)
                if start_date <= converted_date <= end_date:
                    title = json_dict['title']
                    tags = []
                    for tag in json_dict['postTags']:
                        tags.append(tag['slug'])                    
                    converted_tags = SubstackArchivesDownloader.convert_tags_to_string(tags)
                    canonical_url = json_dict['canonical_url']
                    self._url_cache.append_article_tuple(converted_date, title, converted_tags, canonical_url)

    def _convert_article_tuples_to_pdfs(self, tuples: list[ArticleTuple]):
        # Determine the domain folder name from the URL
        url_to_parse = self._url_cache.get_substack_url() or self._url_cache.get_archive_url()
        parsed_url = urlparse(url_to_parse)
        domain_folder = parsed_url.netloc
        
        # Clean the folder name and create the path
        domain_folder = helper.clean_filename(domain_folder, allow_dots=True)
        output_subfolder = os.path.join(self._directory.output_path, domain_folder)
        
        # Ensure the subfolder exists
        if not os.path.exists(output_subfolder):
            os.makedirs(output_subfolder)
            
        for article_tuple in tuples:
            date, title, tags, url = article_tuple
            filename_output = f'{date} - {tags}{helper.clean_filename(title)}.pdf'
            filename_path_output = os.path.join(output_subfolder, filename_output)
            if os.path.isfile(filename_path_output):
                logger.debug(f"Skipping already downloaded: {title}")
                continue
            logger.info(f"Downloading: {title}")
            self._driver.get(url)
            
            if self.remove_comments:
                self._remove_comments_section()
                
            self._save_current_page_as_pdf_in_output_folder(filename_path_output)
            time.sleep(3)

    def _remove_comments_section(self):
        selectors = [
            '#discussion',
            '.comments-section',
            '.discussion',
            'div[data-component-name="CommentsSection"]',
            '#comment-list',
            'div.comments-list',
            'div.post-footer'
        ]
        
        js_script = """
        arguments[0].forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => el.remove());
        });
        """
        try:
            self._driver.execute_script(js_script, selectors)
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Could not remove comments section: {e}")

    @staticmethod
    def extract_substack_subdomain(sign_in_url: str):
        sub_domain_idx = sign_in_url.find('for_pub=') + len('for_pub=')
        return sign_in_url[sub_domain_idx:]

    @staticmethod
    def convert_json_date_to_yyyymmdd(post_date: str) -> int:
        return int(datetime.strptime(post_date, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y%m%d'))

    @staticmethod
    def convert_tags_to_string(tags: []):
        if tags:
            return ', '.join(tags) + ' - '
        else:
            return ''


class Cache:
    def __init__(self, validated_url: str):
        self._root_url = validated_url if validated_url[-1] != '/' else validated_url[:-1]
        self._archive_url = self._root_url + '/archive'
        self._article_tuples: list[ArticleTuple] = []
        self._substack_url = None

    def get_archive_url(self):
        return self._archive_url

    def set_substack_url(self, subdomain: str):
        self._substack_url = f"https://{subdomain}.substack.com"

    def get_substack_url(self):
        return self._substack_url

    def get_archive_api_url(self):
        if self._substack_url:
            return self._substack_url + '/api/v1/archive'
        if self._root_url:
            return self._root_url + '/api/v1/archive'
        raise exceptions.SubstackUrlNotSet()

    def append_article_tuple(self, date: ArticlePostDate, title: ArticleTitle, tags: ArticleTags, url: ArticleUrl):
        self._article_tuples.append((date, title, tags, url))

    def get_cache_size(self) -> int:
        return len(self._article_tuples)

    def is_cache_empty(self) -> bool:
        return len(self._article_tuples) == 0

    def get_article_tuples_by_date(self, date: int) -> list[ArticleTuple]:
        output = []
        for article in self._article_tuples:
            article_date, _, _, _ = article
            if date == article_date:
                output.append(article)
        return output

    def get_article_tuples_by_date_range(self, start_date: ArticlePostDate,
                                         end_date: ArticlePostDate) -> list[ArticleTuple]:
        assert end_date >= start_date
        output = []
        for article in self._article_tuples:
            article_date, _, _, _ = article
            if start_date <= article_date <= end_date:
                output.append(article)
        return output

    def get_article_tuple_by_idx(self, idx: int) -> ArticleTuple:
        return self._article_tuples[idx]

    def get_latest_article_tuple(self) -> ArticleTuple:
        return self._article_tuples[0]

    def get_earliest_article_tuple(self) -> ArticleTuple:
        return self._article_tuples[-1]

    def get_most_recent_k_article_tuples(self, k: int) -> list[ArticleTuple]:
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
