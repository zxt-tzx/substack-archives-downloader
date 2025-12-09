# Substack Archives Downloader

You just paid for a Substack subscription to your favorite author and would like to download past articles from the archive. This tool does that.

This program uses Selenium to fire up a browser, log into the user-provided Substack account, and download articles as PDF files. Users can choose to download articles falling within a certain date range or to download a user-specified number of most recently published articles.

## Quick Start

1. Ensure you have [uv](https://docs.astral.sh/uv/getting-started/installation/) installed.
2. Clone the repository and navigate to the project directory.
3. (Optional but Recommended) Create a `.env` file for configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials and preferences
   ```
4. Run the program:
   ```bash
   uv run main.py
   ```
5. Follow the instructions in the command line (if not fully configured via `.env`).

> **Note**: ChromeDriver is managed automatically, so no need to download it manually.

## Configuration (.env)

You can skip manual input by setting up a `.env` file. See `.env.example` for a template.

| Variable | Description |
|----------|-------------|
| `SUBSTACK_EMAIL` | Your Substack login email. |
| `SUBSTACK_PASSWORD` | Your Substack login password. |
| `SUBSTACK_URL` | The URL of the newsletter (e.g., `https://author.substack.com/`). |
| `HEADLESS` | Set to `true` to run the browser in the background, `false` to see it. |
| `REMOVE_COMMENTS` | Set to `true` to remove the "Discussion" section from downloaded PDFs. |
| `DOWNLOAD_PODCASTS` | Set to `true` to include podcast posts in the download. |
| `DOWNLOAD_MODE` | Set to `date` (for date range) or `count` (for recent N articles). |
| `ARTICLE_COUNT` | Number of articles to download (if mode is `count`). |
| `DATE_RANGE_START` | Start date in YYYYMMDD format (if mode is `date`). |
| `DATE_RANGE_END` | End date in YYYYMMDD format (if mode is `date`). |

## Development

### Running Tests

This project uses `pytest` for testing. To run the tests, use the following command:

```bash
uv run pytest
```

This will run all tests and generate a coverage report.

To run only unit tests (excluding integration tests that require a browser):

```bash
uv run pytest -m "not integration"
```

## Changelog

- **December 2025**
  - **Testing**: Migrated to `pytest` with coverage reporting and improved test structure.
  - **Environment Variables**: Full support for `.env` file to store credentials and preferences.
  - **Modern Selenium**: Updated to Selenium 4 with `webdriver-manager` for automatic driver management.
  - **Robustness**: Improved login handling (including CAPTCHA detection) and cleanup logic.
  - **Features**: Added option to strip comments from PDFs.
  - **Logging**: Replaced print statements with a proper logging system.
  - **Session Persistence**: Implemented cookie saving to bypass CAPTCHA in headless mode.
- **May 2022**
  - Modify element selectors due to new Substack sign-in UX
- **February 2022**
  - Update to support Substack newsletters hosted on custom domain
  - Load article metadata into cache using API instead of scrolling through archive page
  - Headless browser now works properly
- **August 2021**: Create initial working version

## How It Works

There are two main classes involved in doing the actual work of downloading the PDF files—`PDFDownloader` and `SubstackArchivesDownloader`. The latter is then wrapped in a user interface object to provide a command line interface for the user.

### PDFDownloader

`PDFDownloader` is meant to contain more general methods for downloading PDFs in general. In the future, if I want to do web-scraping involving downloading PDFs from other website, I would extend `PDFDownloader`.

Specifically, `PDFDownloader` is responsible for:

- Initializing the driver with the appropriate settings, depending on whether the browser will be run in the foreground or behind-the-scenes
- Converting the current page the driver is on into PDF.
  - If the browser is running in the foreground, this involves the creation of a temp folder, downloading the PDF file, renaming it, and sending it to the output folder.
  - If the browser is running behind-the-scenes, the page is saved as a PDF to the output folder directly.
- Methods to do with waiting for the page or elements therein to finish loading.

The classes `Directory` and `WaitTime` help `PDFDownloader` fulfill the responsibilities outlined above.

### SubstackArchivesDownloader

`SubstackArchivesDownloader` extends `PDFDownloader` to include methods specific to downloading Substack archives. To do this, it depends on related classes like `UserCredential` and `Cache` to store the user-provided input credentials and the metadata of articles to be downloaded respectively.

After initialization, `SubstackArchivesDownloader` logs in using the user-provided credentials and uses the Substack API (`/api/v1/archive`) to load the metadata of articles to be downloaded (URL, title, and publication date) into `Cache`. It then goes to each article's URL and saves it as a PDF file.

## To-Do List

- [ ] Use a library to create a nicer command line interface. ([This](https://github.com/google/python-fire) looks promising.)
- [ ] Improve input validation and exception-handling.
- [x] Write tests for the project. (Migrated to pytest with coverage)
- [ ] More options on saving as PDF (e.g. `printBackground`, page size etc.)

## Why It’s OK to Download the Archive

> It is very important to clearly define what a subscriptions means. First, it’s not a donation: it is asking a customer to pay money for a product. What, then, is the product? It is not, in fact, any one article (a point that is missed by the misguided focus on micro-transactions). Rather, a subscriber is paying for the regular delivery of well-defined value.
> Each of those words is meaningful:
>
> - *Paying*: A subscription is an ongoing commitment to the *production* of content, not a one-off payment for one piece of content that catches the eye.
> - *Regular Delivery*: A subscriber does not need to depend on the random discovery of content; said content can be delivered to the subscriber directly, whether that be email, a bookmark, or an app.
> - *Well-defined Value*: A subscriber needs to know what they are paying for, and it needs to be worth it.
>
> —<cite>Ben Thompson, [The Local News Business Model](https://stratechery.com/2017/the-local-news-business-model/)</cite>
