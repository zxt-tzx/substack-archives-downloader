# Substack Archives Downloader

You just paid for a Substack subscription to your favorite author and would like to download past articles from the archive. This tool does that.

This program uses Selenium to fire up a browser, log into the user-provided Substack account, and download articles as PDF files. Users can choose to download articles falling within a certain date range or to download a user-specified number of most recently published articles.

## Quick Start

1. Ensure you have [uv](https://docs.astral.sh/uv/getting-started/installation/) installed.
2. Run the program:
   ```bash
   uv run main.py
   ```
3. Follow the instructions shown in the command line.

> Note: ChromeDriver is now managed automatically, so no need to download it manually.


## Changelog

- May 2022
  - Modify element selectors due to new Substack sign-in UX
- February 2022
  - Update to support Substack newsletters hosted on custom domain
  - Load article metadata into cache using API instead of scrolling through archive page
  - Headless browser now works properly
- August 2021: Create initial working version

## How It Works

There are two classes involved in doing the actual work of downloading the PDF files—`PDFDownloader` and `SubstackArchivesDownloader`. The latter is then wrapped in a user interface object to provide a command line interface for the user.

### PDFDownloader

`PDFDownloader` is meant to contain more general methods for downloading PDFs in general. In the future, if I want to do web-scraping involving downloading PDFs from other website, I would extend `PDFDownloader`.

Specifically, `PDFDownloader` is responsible for:

- Initializing the driver with the appropriate settings, depending on whether the browser will be run in the foreground or behind-the-scenes
- Converting the current page the driver is on into PDF.
  - If the browser is running in the foreground, this involves the creation of a temp folder, downloading the PDF file, renaming it, and sending it to the output folder. The reason for this complication is Selenium is unable to directly change the file name when running the command `driver.execute_script('window.print();')`. The temp folder will be deleted at the end of the program, so the output should be the same as if the browser ran behind-the-scenes.
  - If the browser is running behind-the-scenes, the page is saved as a PDF to the output folder directly.
- Methods to do with waiting for the page or elements therein to finish loading.

The classes `Directory` and `WaitTime` help `PDFDownloader` fulfill the responsibilities outlined above.

### SubstackArchivesDownloader

`SubstackArchivesDownloader` extends `PDFDownloader` to include methods specific to downloading Substack archives. To do this, it depends on related classes like `UserCredential` and `Cache` to store the user-provided input credentials and the metadata of articles to be downloaded respectively.

After initialization, `SubstackArchivesDownloader` logs in using the user-provided credentials and uses `https://subdomain.substack.com/api/v1/archive` to load the metadata of articles to be downloaded (URL, title, and publication date) into `Cache`. It then goes to each article's URL and saves it as a PDF file.

## To-Do List

- [High] Use a library to create a nicer command line interface. ([This](https://github.com/google/python-fire) looks promising.)
- [Medium] Improve input validation and exception-handling (came across [this](https://dev.to/rinaarts/declutter-your-python-code-with-error-handling-decorators-2db9)).
- [Low] Write tests for the project and set up a continuous integration pipeline on GitHub. This would help to prevent breaking changes to the code as updates are made.
- [Low] More options on saving as PDF (e.g. `printBackground`, page size etc.)

## For Further Extension

- To convert articles into PDF, the browser must visit each article while logged into an account with a subscription. Currently, this is achieved through the user entering their username and password into the program directly.
  - However, a downside of the current implementation is that less sophisticated might not be able to clone a GitHub project and run it on their local machine.
  - A possible solution is to convert this current project into an executable application. (Brief Googling reveals `pyinstaller` might be able to achieve this.) But I don’t think unsophisticated users should be in the habit of downloading and running random executable files from the Internet…
- Another possible solution is to create a web app that downloads the relevant PDFs and transmits them to the user in the form of a .zip file.
  - Unfortunately, this still requires the user to provide their username and password, this time to a random application on the Internet. I don’t think there is any way to provide assurance that the server is not secretly collecting their username and password.
  - Strictly speaking, the user could simply use a temporary password, download the relevant files, then change the password after using the web app. But even then, the user is still exposed to potential mischief by the web app during the downloading process…
- Yet another possible solution is to create a Chrome extension so that the user can log in on her own and use the Chrome extension to automate the downloading of PDFs. Further research is required to see whether this solution is feasible.

## Why It’s OK to Download the Archive

> It is very important to clearly define what a subscriptions means. First, it’s not a donation: it is asking a customer to pay money for a product. What, then, is the product? It is not, in fact, any one article (a point that is missed by the misguided focus on micro-transactions). Rather, a subscriber is paying for the regular delivery of well-defined value.
> Each of those words is meaningful:
>
> - *Paying*: A subscription is an ongoing commitment to the *production* of content, not a one-off payment for one piece of content that catches the eye.
> - *Regular Delivery*: A subscriber does not need to depend on the random discovery of content; said content can be delivered to the subscriber directly, whether that be email, a bookmark, or an app.
> - *Well-defined Value*: A subscriber needs to know what they are paying for, and it needs to be worth it.
>
> —<cite>Ben Thompson, [The Local News Business Model](https://stratechery.com/2017/the-local-news-business-model/)</cite>
