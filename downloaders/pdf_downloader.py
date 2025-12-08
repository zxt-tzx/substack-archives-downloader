from base64 import b64decode
import json
import os
import random
import shutil

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from utilities import exceptions
from utilities.logging_config import get_logger

logger = get_logger("pdf_downloader")


class PDFDownloader:
    """
    To have a more abstract class which can be repurposed to download PDFs in general
    with no assumption that it's supposed to download from Substack or that any login is required
    """

    def __init__(self, is_headless: bool = False):
        self._is_headless = is_headless
        self._directory = Directory(self._is_headless)
        self._driver = self._initialize_driver()
        self._wait_time = WaitTime()  # randomized wait time

    # Methods for managing PDFDownloader's life cycle
    def _initialize_driver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--incognito')
        chrome_options.add_argument('--window-size=1920,1080')

        if self._is_headless:
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
                'savefile.default_directory': self._directory.temp_path
            }
            chrome_options.add_experimental_option('prefs', profile)
            chrome_options.add_argument('--kiosk-printing')

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def shut_down(self):
        try:
            if not self._is_headless:
                self._directory.delete_temp_folder()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
        finally:
            try:
                self._driver.quit()
            except Exception as e:
                logger.warning(f"Could not quit driver: {e}")

    # Methods for generating PDF
    def _save_current_page_as_pdf_in_output_folder(self, output_path_with_filename: str):
        if self._is_headless:
            self._write_to_local_file_in_output_folder(output_path_with_filename)
        else:
            self._write_to_temp_folder_and_move_to_output_folder(output_path_with_filename)

    def _write_to_local_file_in_output_folder(self, output_path_with_filename: str):
        b64_data = self._driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
        })['data']
        b64_data_decoded = b64decode(b64_data, validate=True)
        PDFDownloader.validate_b64_string_is_pdf(b64_data_decoded)
        with open(output_path_with_filename, "wb") as f:
            f.write(b64_data_decoded)

    # Methods to do with waiting
    def _write_to_temp_folder_and_move_to_output_folder(self, filename_path_output: str):
        self._driver.execute_script('window.print();')  # download PDF to temp directory
        # move file from temp directory to output directory and rename file
        for _, _, filenames in os.walk(self._directory.temp_path):
            for filename in filenames:  # should only ever have one file in temp, but you never know. just in case.
                if filename.lower().endswith('.pdf'):
                    filename_temp = filenames[0]
                    filename_path_temp = os.path.join(self._directory.temp_path, filename_temp)
                    os.rename(filename_path_temp, filename_path_output)

    # not sure if there is a better way of doing this; return boolean so exact exception can vary depending on context
    def _wait_for_element_to_load(self, by: type(By), element_target: str) -> bool:
        try:
            WebDriverWait(self._driver, self._wait_time.max_wait_time).until(
                EC.presence_of_element_located((by, element_target)))
            return True
        except TimeoutException:
            logger.warning("Timeout exception while waiting for element to load")
            return False

    @staticmethod
    def validate_b64_string_is_pdf(b64_string: bytes):
        if b64_string[0:4] != b'%PDF':
            raise ValueError('Missing PDF file signature')


class Directory:
    def __init__(self, is_headless: bool):
        self._path_to_directory = os.path.dirname(__file__)
        self.output_path = os.path.join(self._path_to_directory, '../output')
        self._ensure_output_folder_exists()
        if not is_headless:
            self.temp_path = os.path.join(self._path_to_directory, 'temp')
            self._ensure_temp_folder_exists()
            self._check_temp_folder_is_empty()

    # Methods used in initialization
    def _ensure_temp_folder_exists(self):
        Directory.ensure_folder_exists(self.temp_path)

    def _check_temp_folder_is_empty(self):
        Directory.check_folder_is_empty(self.temp_path)

    def _ensure_output_folder_exists(self):
        Directory.ensure_folder_exists(self.output_path)

    # Tell Directory object to delete its temp folder (as part of wrapping up the program)
    def delete_temp_folder(self):
        try:
            if os.path.isdir(self.temp_path):
                shutil.rmtree(self.temp_path)
        except Exception as e:
            logger.warning(f"Could not delete temp folder: {e}")

    @staticmethod
    def ensure_folder_exists(path_to_folder: str):
        if not os.path.isdir(path_to_folder):
            os.mkdir(path_to_folder)

    @staticmethod
    def check_folder_is_empty(path_to_folder: str):
        if len(os.listdir(path_to_folder)) != 0:
            raise (exceptions.TempFolderNotEmpty(path_to_folder))


class WaitTime:
    def __init__(self):
        # in seconds
        self._short_wait_time = 0.5
        self._short_wait_time_interval = 0.2
        self._long_wait_time = 3
        self._long_wait_time_interval = 0.5
        self.max_wait_time = 10

    def get_short_wait_time(self):
        return WaitTime.generate_random_float_within_interval(self._short_wait_time, self._short_wait_time_interval)

    def get_long_wait_time(self):
        return WaitTime.generate_random_float_within_interval(self._long_wait_time, self._long_wait_time_interval)

    @staticmethod
    def generate_random_float_within_interval(average: float, interval: float) -> float:
        return random.uniform(average - interval, average + interval)
