import os

from sec_edgar_downloader import Downloader


def download_filings(company_name, email, filing_type="10-K", count=2):
    """
    Download SEC filings for a given company.

    Args:
        company_name (str): Name of the company (e.g., "Tesla").
        email (str): Email address for SEC EDGAR compliance.
        filing_type (str): Type of filing to download (default: "10-K").
        count (int): Number of filings to download (default: 2).
    """
    # Set up downloader with compliant User-Agent
    downloader = Downloader(os.path.join(os.getcwd(), "data/raw"))
    downloader.set_user_agent(email)

    # Download filings
    downloader.get(filing_type, company_name, count=count)


if __name__ == "__main__":
    # Example usage
    company_name = "Tesla"
    email = "your_email@example.com"  # Replace with your email
    download_filings(company_name, email)
