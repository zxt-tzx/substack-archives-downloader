import os
import unittest
from unittest.mock import MagicMock
from dotenv import load_dotenv

from downloaders.substack_archives_downloader import SubstackArchivesDownloader

class TestIntegration(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.email = os.getenv("SUBSTACK_EMAIL")
        self.password = os.getenv("SUBSTACK_PASSWORD")
        self.url = os.getenv("SUBSTACK_URL")
        
        if not (self.email and self.password and self.url):
            self.skipTest("Skipping integration test: Missing credentials in .env")

    def test_login_flow(self):
        """
        Tests that we can launch the browser, navigate to sign in, and enter credentials.
        This test stops short of actually downloading to avoid excessive scraping in tests.
        """
        print(f"\nTesting login for {self.url}...")
        downloader = SubstackArchivesDownloader(self.url, is_headless=True)
        
        try:
            # We call the internal login methods to test them step-by-step or just the main public one
            downloader.log_in(self.email, self.password)
            
            # If no exception was raised, we assume success for this basic check
            self.assertTrue(downloader._signed_in, "Downloader should mark itself as signed in")
            
        except Exception as e:
            self.fail(f"Login failed with exception: {e}")
        finally:
            downloader.shut_down()

if __name__ == '__main__':
    unittest.main()

