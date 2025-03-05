import io
import shutil
import tempfile
from pathlib import Path
from urllib.request import urlopen

import stamina

from .shell_utils import run_command_with_merged_output
from .validator_utils import is_secure_public_url

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


def _add_trusted_cert(*, cert_path: Path, keychain: Path) -> None:
    """
    Helper function to add the certificate at `cert_path` to the specified
    `keychain` using the 'security import' command instead of 'security
    add-trusted-cert'.

    The 'security add-trusted-cert' command would be preferred because it
    explicitly sets the certificate as trusted for all users. However, it
    requires interactive approval in macOS, which makes it unsuitable for
    automated environments like CI/CD.

    Instead, we use 'security import' to add the certificate to the keychain
    without modifying trust settings. This allows codesigning and notarization
    processes to work without requiring user interaction.
    """
    command = [
        "security",
        "import",
        str(cert_path),
        "-k",
        str(keychain),
        "-T",
        "/usr/bin/codesign",
    ]
    run_command_with_merged_output(command)


@stamina.retry(attempts=3, on=Exception)
def _fetch_apple_g2_ca_certificate(certificate_url: str) -> io.BytesIO:
    """
    Fetch the Apple G2 CA certificate from the given URL and return it as a
    BytesIO object.
    """

    if not is_secure_public_url(certificate_url):
        print("Invalid Apple G2 CA certificate URL, skipping")
        raise ValueError(f"Invalid Apple G2 CA certificate URL: {certificate_url}")

    cert_data = io.BytesIO()
    with urlopen(certificate_url) as response:  # noqa: S310
        shutil.copyfileobj(response, cert_data)

    cert_data.seek(0)
    return cert_data


def install_apple_g2_ca_certificate(
    *,
    keychain: Path | None = None,
    certificate_url: str = DEFAULT_APPLE_G2_CA_URL,
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

    print(f"Downloading Apple G2 CA certificate from {certificate_url}")
    cert_data = _fetch_apple_g2_ca_certificate(certificate_url)

    # Save the downloaded certificate data to a temporary file.
    with tempfile.NamedTemporaryFile(suffix=".cer") as temp_cert:
        cert_file_path = Path(temp_cert.name)
        shutil.copyfileobj(cert_data, temp_cert)
        temp_cert.flush()
        print(f"Certificate downloaded and saved to temporary file: {cert_file_path}")

        print(f"Installing certificate into keychain: {keychain}")
        _add_trusted_cert(cert_path=cert_file_path, keychain=keychain)
        print("Apple G2 CA certificate installed successfully.")
