import pytest
from downloaders.substack_archives_downloader import SubstackArchivesDownloader

@pytest.mark.integration
def test_login_flow(substack_credentials):
    """
    Tests that we can launch the browser, navigate to sign in, and enter credentials.
    This test stops short of actually downloading to avoid excessive scraping in tests.
    """
    email = substack_credentials["email"]
    password = substack_credentials["password"]
    url = substack_credentials["url"]
    
    print(f"\nTesting login for {url}...")
    # Initialize with headless mode for CI/test environments
    downloader = SubstackArchivesDownloader(url, is_headless=True)
    
    try:
        # We call the internal login methods to test them step-by-step or just the main public one
        downloader.log_in(email, password)
        
        # If no exception was raised, we assume success for this basic check
        assert downloader._signed_in, "Downloader should mark itself as signed in"
        
    except Exception as e:
        pytest.fail(f"Login failed with exception: {e}")
    finally:
        downloader.shut_down()
