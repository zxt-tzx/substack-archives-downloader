import pytest
from utilities import helper
from utilities import exceptions
from downloaders.substack_archives_downloader import SubstackArchivesDownloader

class TestHelper:
    def test_input_is_url(self):
        assert helper.input_is_url("https://example.com") is None
        assert helper.input_is_url("http://sub.domain.com/path") is None
        
        with pytest.raises(exceptions.NotUrlException):
            helper.input_is_url("not a url")
            
    def test_clean_filename(self):
        assert helper.clean_filename("Normal Title") == "Normal Title"
        assert helper.clean_filename("Title/With/Slashes") == "Title_With_Slashes"
        assert helper.clean_filename("Title: With Colons") == "Title_ With Colons"
        
    def test_input_email_validation(self):
        assert helper.input_email_validation("test@example.com") is None
        
        with pytest.raises(exceptions.UsernameNotEmail):
            helper.input_email_validation("invalid-email")
            
        with pytest.raises(exceptions.UsernameNotEmail):
            helper.input_email_validation("test@")

class TestSubstackArchivesDownloader:
    def test_extract_substack_subdomain(self):
        url = "https://substack.com/sign-in?redirect=%2Farchive&for_pub=example"
        assert SubstackArchivesDownloader.extract_substack_subdomain(url) == "example"
        
    def test_convert_json_date(self):
        # 2021-10-12T14:52:58.738Z
        json_date = "2021-10-12T14:52:58.738Z"
        expected = 20211012
        assert SubstackArchivesDownloader.convert_json_date_to_yyyymmdd(json_date) == expected
        
    def test_convert_tags(self):
        tags = ["tag1", "tag2"]
        expected = "tag1, tag2 - "
        assert SubstackArchivesDownloader.convert_tags_to_string(tags) == expected
        
        assert SubstackArchivesDownloader.convert_tags_to_string([]) == ""
