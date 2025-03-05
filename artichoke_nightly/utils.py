import ipaddress
from urllib.parse import urlparse

import validators


def is_secure_public_url(url: str) -> bool:
    """
    Validate that the URL is syntactically correct, uses HTTPS,
    and its hostname is not an IP address.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL meets the criteria, False otherwise.
    """
    # Check if the URL is syntactically valid.
    if not validators.url(url):
        return False

    parsed = urlparse(url)

    # Assert that the scheme is HTTPS.
    if parsed.scheme.lower() != "https":
        return False

    # Assert that the hostname is not an IP address.
    hostname = parsed.hostname
    if hostname is None:
        return False

    try:
        ipaddress.ip_address(hostname)
        # If no exception is raised, the hostname is an IP address.
    except ValueError:
        # Not an IP address.
        return True
    else:
        return False


# Example usage:
if __name__ == "__main__":
    test_urls = [
        "https://www.example.com",  # Expected: True
        "https://github.com",  # Expected: True
        "http://www.example.com",  # Expected: False (not https)
        "https://127.0.0.1",  # Expected: False (hostname is an IP)
        "https://192.168.1.1",  # Expected: False (hostname is an IP)
        "ftp://www.example.com",  # Expected: False (not https)
    ]

    for url in test_urls:
        print(f"{url!r}: {is_secure_public_url(url)}")
