import tempfile
from pathlib import Path
from urllib.request import urlopen

import stamina

from .shell_utils import run_command_with_merged_output
from .utils import is_secure_public_url

# Default URL for Apple's Worldwide Developer Relations G2 CA certificate.
#
# All of Apple's CAs can be found at: https://www.apple.com/certificateauthority/.
#
# The Developer ID Application certificate used for codesigning has "Developer
# ID - G2 (Expiring 09/17/2031 00:00:00 UTC)" as an intermediate in its
# certificate chain.
DEFAULT_APPLE_G2_CA_URL = (
    "https://www.apple.com/certificateauthority/AppleRootCA-G2.cer"
)


@stamina.retry(attempts=3, on=Exception)
def _add_trusted_cert(cert_path: Path, keychain: Path) -> None:
    """
    Helper function to add the certificate at `cert_path` to the specified `keychain`
    using the 'security add-trusted-cert' command. This function is retried up to three
    times with exponential backoff (via stamina) to mitigate transient failures.
    """
    command = [
        "security",
        "add-trusted-cert",
        "-d",  # Add certificate as trusted for all users.
        "-r",
        "trustRoot",  # Set trust settings to trust as root.
        "-k",
        str(keychain),
        str(cert_path),
    ]
    run_command_with_merged_output(command)


def install_apple_g2_ca_certificate(
    certificate_url: str = DEFAULT_APPLE_G2_CA_URL, keychain: Path | None = None
) -> None:
    """
    Download and install Apple's Worldwide Developer Relations G2 CA certificate
    (Apple G2 CA) into a specified keychain using the macOS 'security' command.

    If no keychain is provided, the certificate will be installed into the
    system keychain at: /Library/Keychains/System.keychain

    This function is designed to be part of the Apple codesigning and
    notarization process, ensuring that the required certificate chain is
    trusted on the system. It uses the `stamina` library to retry the
    installation in case of transient errors.

    Args:
        certificate_url (str): URL from which to download the certificate.
                                 Defaults to Apple's official certificate URL.
        keychain (Path, optional): The keychain to install the certificate into.
                                   Defaults to the system keychain if None.
    """
    if keychain is None:
        keychain = Path("/Library/Keychains/System.keychain")

    if not is_secure_public_url(certificate_url):
        print("Invalid Apple G2 CA certificate URL, skipping")
        return

    print(f"Downloading Apple G2 CA certificate from {certificate_url}")
    cert_data = None
    try:
        for attempt in stamina.retry_context(attempts=3, on=Exception):
            with (
                attempt,
                urlopen(certificate_url, timeout=10) as response,  # noqa: S310
            ):
                cert_data = response.read()
    except Exception as e:
        print(f"Error downloading certificate: {e}")
        raise

    assert cert_data is not None, "Failed to download certificate data"  # noqa: S101

    # Save the downloaded certificate data to a temporary file.
    with tempfile.NamedTemporaryFile(suffix=".cer") as temp_cert:
        cert_file_path = Path(temp_cert.name)
        temp_cert.write(cert_data)
        print(f"Certificate downloaded and saved to temporary file: {cert_file_path}")

        print(f"Installing certificate into keychain: {keychain}")
        _add_trusted_cert(cert_file_path, keychain)
        print("Apple G2 CA certificate installed successfully.")
