from base64 import b64decode
import json
import os
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utilities import errors


class PDFDownloader:
    """
    To have a more abstract class which can be repurposed to download PDFs in general
    with no assumption that it's supposed to download from Substack or that any login is required
    """

    def __init__(self, is_headless: bool = False):
        self.is_headless = is_headless
        self.directory = Directory(self.is_headless)
        self.driver = self.initialize_driver(self.is_headless)
        self.wait_time = WaitTime()

    # Methods for managing PDFDownloader's life cycle
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
                'savefile.default_directory': self.directory.temp_path
            }
            chrome_options.add_experimental_option('prefs', profile)
            chrome_options.add_argument('--kiosk-printing')

        return webdriver.Chrome(options=chrome_options, executable_path=self.directory.chromedriver_path)

    def shut_down(self):
        if not self.is_headless:
            self.directory.delete_temp_folder()
        self.driver.quit()

    # Methods for generating PDF
    def save_current_page_as_pdf_in_output_folder(self, output_path_with_filename: str):
        if self.is_headless:
            self.write_to_local_file_in_output_folder(output_path_with_filename)
        else:
            self.write_to_temp_folder_and_move_to_output_folder(output_path_with_filename)

    def write_to_local_file_in_output_folder(self, output_path_with_filename: str):
        b64_data = self.driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
        })['data']
        b64_data_decoded = b64decode(b64_data, validate=True)
        PDFDownloader.validate_b64_string(b64_data_decoded)
        with open(output_path_with_filename, "wb") as f:
            f.write(b64_data_decoded)

    # Methods to do with waiting
    def write_to_temp_folder_and_move_to_output_folder(self, filename_path_output: str):
        self.driver.execute_script('window.print();')  # download PDF to temp directory
        # move file from temp directory to output directory and rename file
        for _, _, filenames in os.walk(self.directory.temp_path):
            for filename in filenames:  # should only ever have one file in temp, but you never know. just in case.
                if filename.lower().endswith('.pdf'):
                    filename_temp = filenames[0]
                    filename_path_temp = os.path.join(self.directory.temp_path, filename_temp)
                    os.rename(filename_path_temp, filename_path_output)

    def wait_for_element_to_load(self, by: By, element_target: str) -> bool:
        try:
            WebDriverWait(self.driver, self.wait_time.max_wait_time).until(
                EC.presence_of_element_located((by, element_target)))
            return True
        except TimeoutException:
            print("Timeout exception while waiting for element to load")
            return False

    # TODO figure out how to wait for async javascript to finish loading
    #  1. Look into polling2
    #  2. If on Java, this looks promising: https://github.com/swtestacademy/JSWaiter/tree/master/src/test/java
    #  Tried and failed:
    #  WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
    #  WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return "return jQuery.active') == '0')
    def wait_for_page_to_finish_loading(self):  # TODO WIP
        try:
            WebDriverWait(self.driver, self.wait_time.max_wait_time).until(
                staleness_of(self.driver.find_element_by_tag_name('html')))
            return True
        except TimeoutException:
            print("Timeout exception while waiting for [age to load")
            return False

    @staticmethod
    def validate_b64_string(b64_string: bytes):
        if b64_string[0:4] != b'%PDF':
            # TODO use more specific error?
            raise ValueError('Missing the PDF file signature')


class Directory:
    # TODO methods to set different directories?
    def __init__(self, is_headless: bool):
        self.path_to_directory = os.path.dirname(__file__)
        self.chromedriver_path = os.path.join(self.path_to_directory, '../utilities/chromedriver')
        self.output_path = os.path.join(self.path_to_directory, '../output')
        self.raise_error_if_chromedriver_missing()
        self.ensure_output_folder_exists()
        if not is_headless:
            self.temp_path = os.path.join(self.path_to_directory, 'temp')
            self.ensure_temp_folder_exists()

    def raise_error_if_chromedriver_missing(self):
        if not os.path.exists(self.chromedriver_path):
            raise errors.ChromedriverMissing(f"chromedriver does not exist at {self.chromedriver_path}")

    def ensure_temp_folder_exists(self):
        Directory.ensure_folder_exists(self.temp_path)

    def ensure_output_folder_exists(self):
        Directory.ensure_folder_exists(self.output_path)

    def delete_temp_folder(self):
        os.rmdir(self.temp_path)  # remove empty directory
        # shutil.rmtree(self.temp_path)  # delete directory and all its contents

    @staticmethod
    def ensure_folder_exists(path_to_folder: str):
        if not os.path.isdir(path_to_folder):
            os.mkdir(path_to_folder)


class WaitTime:
    # TODO include setters to modify wait_time?
    def __init__(self):
        # in seconds
        self.short_wait_time = 0.5
        self.short_wait_time_interval = 0.2
        self.long_wait_time = 3
        self.long_wait_time_interval = 0.5
        self.max_wait_time = 10

    def get_short_wait_time(self):
        return WaitTime.generate_random_float_within_interval(self.short_wait_time, self.short_wait_time_interval)

    def get_long_wait_time(self):
        return WaitTime.generate_random_float_within_interval(self.long_wait_time, self.long_wait_time_interval)

    @staticmethod
    def generate_random_float_within_interval(average: float, interval: float) -> float:
        return random.uniform(average - interval, average + interval)
