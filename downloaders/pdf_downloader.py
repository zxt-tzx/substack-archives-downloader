import json
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import TimeoutException

from utilities import errors, helper


class PDFDownloader:
    """
    To have a more abstract class which can be repurposed to download PDFs in general
    with no assumption that it's supposed to download from Substack or that any login is required
    """

    class PathNames:
        # TODO methods to set different directories?
        def __init__(self, is_headless: bool):
            self.path_to_directory = os.path.dirname(__file__)
            self.chromedriver_path = os.path.join(self.path_to_directory, '../utilities/chromedriver')
            self.output_path = os.path.join(self.path_to_directory, '../output')
            self.check_chromedriver_exists()
            self.check_output_folder_exists()
            if not is_headless:
                self.temp_path = os.path.join(self.path_to_directory, 'temp')
                self.check_temp_folder_exists()

        def check_chromedriver_exists(self):
            if not os.path.exists(self.chromedriver_path):
                raise errors.ChromedriverMissing(f"chromedriver does not exist at {self.chromedriver_path}")

        def check_temp_folder_exists(self):
            if not os.path.isdir(self.temp_path):
                os.mkdir(self.temp_path)

        def check_output_folder_exists(self):
            if not os.path.isdir(self.output_path):
                os.mkdir(self.output_path)

        def delete_temp_folder(self):
            os.rmdir(self.temp_path)  # remove empty directory
            # shutil.rmtree(self.temp_path)  # delete directory and all its contents

    class Waits:
        # TODO include setters to modify waits?
        def __init__(self):
            # in seconds
            self.short_wait_time = 0.5
            self.short_wait_time_interval = 0.2
            self.long_wait_time = 3
            self.long_wait_time_interval = 0.5
            self.max_wait_time = 10

        def get_short_wait_time(self):
            return helper.generate_random_float_within_interval(self.short_wait_time, self.short_wait_time_interval)

        def get_long_wait_time(self):
            return helper.generate_random_float_within_interval(self.long_wait_time, self.long_wait_time_interval)

    def __init__(self, is_headless: bool = False):
        self.waits = self.Waits()
        self.is_headless = is_headless
        self.path_names = self.PathNames(self.is_headless)
        self.driver = self.initialize_driver(self.is_headless)

    def initialize_driver(self, is_headless):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--incognito')
        chrome_options.add_argument('--window-size=1920,1080')

        if is_headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
        else:
            settings = {
                "recentDestinations": [{
                    "id": "Save as PDF",
                    "origin": "local",
                    "account": "",
                }],
                "selectedDestinationId": "Save as PDF",
                "version": 2,
                "isHeaderFooterEnabled": False,
            }
            profile = {
                'printing.print_preview_sticky_settings.appState': json.dumps(settings),
                'savefile.default_directory': self.path_names.temp_path
            }
            chrome_options.add_experimental_option('prefs', profile)
            chrome_options.add_argument('--kiosk-printing')

        return webdriver.Chrome(options=chrome_options, executable_path=self.path_names.chromedriver_path)

    def wait_for_element_to_load(self, by: By, element_target: str) -> bool:
        try:
            WebDriverWait(self.driver, self.waits.max_wait_time).until(
                EC.presence_of_element_located((by, element_target)))
            return True
        except TimeoutException:
            print("Timeout exception while waiting for element to load")
            return False

    def shut_down(self):
        if not self.is_headless:
            self.path_names.delete_temp_folder()
        self.driver.quit()

    # TODO figure out how to wait for async javascript to finish loading
    #  1. Look into polling2
    #  2. If on Java, this looks promising: https://github.com/swtestacademy/JSWaiter/tree/master/src/test/java
    #  Tried and failed:
    #  WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
    #  WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return "return jQuery.active') == '0')
    def wait_for_page_to_finish_loading(self):
        try:
            WebDriverWait(self.driver, self.waits.max_wait_time).until(
                staleness_of(self.driver.find_element_by_tag_name('html')))
            return True
        except TimeoutException:
            print("Timeout exception while waiting for [age to load")
            return False
