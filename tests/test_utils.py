import unittest
from utilities import helper
from downloaders.substack_archives_downloader import SubstackArchivesDownloader

class TestHelper(unittest.TestCase):
    def test_input_is_url(self):
        self.assertIsNone(helper.input_is_url("https://example.com"))
        self.assertIsNone(helper.input_is_url("http://sub.domain.com/path"))
        
        with self.assertRaises(Exception):
            helper.input_is_url("not a url")
            
    def test_clean_filename(self):
        self.assertEqual(helper.clean_filename("Normal Title"), "Normal Title")
        self.assertEqual(helper.clean_filename("Title/With/Slashes"), "Title_With_Slashes")
        self.assertEqual(helper.clean_filename("Title: With Colons"), "Title_ With Colons")

class TestSubstackArchivesDownloader(unittest.TestCase):
    def test_extract_substack_subdomain(self):
        url = "https://substack.com/sign-in?redirect=%2Farchive&for_pub=example"
        self.assertEqual(SubstackArchivesDownloader.extract_substack_subdomain(url), "example")
        
    def test_convert_json_date(self):
        # 2021-10-12T14:52:58.738Z
        json_date = "2021-10-12T14:52:58.738Z"
        expected = 20211012
        self.assertEqual(SubstackArchivesDownloader.convert_json_date_to_yyyymmdd(json_date), expected)
        
    def test_convert_tags(self):
        tags = ["tag1", "tag2"]
        expected = "tag1, tag2 - "
        self.assertEqual(SubstackArchivesDownloader.convert_tags_to_string(tags), expected)
        
        self.assertEqual(SubstackArchivesDownloader.convert_tags_to_string([]), "")

if __name__ == '__main__':
    unittest.main()

