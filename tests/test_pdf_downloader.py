import os
import shutil
import pytest
from unittest.mock import MagicMock, patch
from downloaders.pdf_downloader import PDFDownloader, Directory, WaitTime
from utilities import exceptions

class TestPDFDownloader:
    def test_validate_b64_string_is_pdf(self):
        # Valid PDF header
        pdf_bytes = b'%PDF-1.4\n...'
        # Should not raise
        PDFDownloader.validate_b64_string_is_pdf(pdf_bytes)
        
        # Invalid header
        with pytest.raises(ValueError, match='Missing PDF file signature'):
            PDFDownloader.validate_b64_string_is_pdf(b'NOT A PDF')

class TestDirectory:
    @pytest.fixture
    def temp_dir_structure(self, tmp_path):
        """Create a temporary directory structure for testing."""
        return tmp_path

    def test_ensure_folder_exists(self, temp_dir_structure):
        new_folder = temp_dir_structure / "new_folder"
        assert not os.path.isdir(new_folder)
        
        Directory.ensure_folder_exists(str(new_folder))
        assert os.path.isdir(new_folder)
        
        # Should be idempotent
        Directory.ensure_folder_exists(str(new_folder))
        assert os.path.isdir(new_folder)

    def test_check_folder_is_empty(self, temp_dir_structure):
        # Empty folder
        empty_folder = temp_dir_structure / "empty"
        empty_folder.mkdir()
        Directory.check_folder_is_empty(str(empty_folder))
        
        # Non-empty folder
        non_empty = temp_dir_structure / "non_empty"
        non_empty.mkdir()
        (non_empty / "file.txt").touch()
        
        with pytest.raises(exceptions.TempFolderNotEmpty):
            Directory.check_folder_is_empty(str(non_empty))

class TestWaitTime:
    def test_generate_random_float(self):
        avg = 10.0
        interval = 1.0
        val = WaitTime.generate_random_float_within_interval(avg, interval)
        assert (avg - interval) <= val <= (avg + interval)

    def test_wait_times(self):
        wt = WaitTime()
        # Test short wait
        short = wt.get_short_wait_time()
        assert (wt._short_wait_time - wt._short_wait_time_interval) <= short <= (wt._short_wait_time + wt._short_wait_time_interval)
        
        # Test long wait
        long_val = wt.get_long_wait_time()
        assert (wt._long_wait_time - wt._long_wait_time_interval) <= long_val <= (wt._long_wait_time + wt._long_wait_time_interval)

