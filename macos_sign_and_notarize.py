#!/usr/bin/env python3

import base64
import binascii
import subprocess
from pathlib import Path
from contextlib import contextmanager
import sys
import secrets
import os
import tempfile
import shutil
import json
import traceback


@contextmanager
def log_group(group):
    print(f"::group::{group}")
    try:
        yield
    finally:
        print("::endgroup::")


@contextmanager
def attach_disk_image(image):
    try:
        with log_group("Attaching disk image"):
            subprocess.run(
                [
                    "/usr/bin/hdiutil",
                    "attach",
                    str(image),
                ],
                check=True,
            )
        mounted_image = Path("/Volumes/Artichoke Ruby nightly")
        yield mounted_image
    finally:
        with log_group("Detatching disk image"):
            subprocess.run(
                ["/usr/bin/hdiutil", "detach", str(mounted_image)],
                check=True,
            )


def emit_metadata():
    if os.getenv("CI") != "true":
        return
    with log_group("Workflow metadata"):
        if repository := os.getenv("GITHUB_REPOSITORY"):
            print(f"GitHub Repository: {repository}")
        if actor := os.getenv("GITHUB_ACTOR"):
            print(f"GitHub Actor: {actor}")
        if workflow := os.getenv("GITHUB_WORKFLOW"):
            print(f"GitHub Workflow: {workflow}")
        if job := os.getenv("GITHUB_JOB"):
            print(f"GitHub Job: {job}")
        if run_id := os.getenv("GITHUB_RUN_ID"):
            print(f"GitHub Run ID: {run_id}")
        if ref := os.getenv("GITHUB_REF"):
            print(f"GitHub Ref: {ref}")
        if ref_name := os.getenv("GITHUB_REF_NAME"):
            print(f"GitHub Ref Name: {ref_name}")
        if sha := os.getenv("GITHUB_SHA"):
            print(f"GitHub SHA: {sha}")


def keychain_path():
    """
    Absolute path to a keychain used for the codesigning and notarization
    process.

    This path is a constant.
    """
    # If running on GitHub Actions, use the `RUNNER_TEMP` directory.
    #
    # `RUNNER_TEMP` is the path to a temporary directory on the runner. This
    # directory is emptied at the beginning and end of each job.
    if runner_temp := os.getenv("RUNNER_TEMP"):
        return Path(runner_temp).joinpath("notarization.keychain-db")
    else:
        return Path("notarization.keychain-db").resolve()


def notarytool_credentials_profile():
    """
    Name of the credentials profile stored in the build keychain for use with
    notarytool.

    This profile is a constant.
    """
    return "artichoke-apple-codesign-notarize"


def codesigning_identity():
    """
    Codesigning identity and name of the Apple Developer ID Application.
    """
    return "Developer ID Application: Ryan Lopopolo (VDKP67932G)"


def notarization_apple_id():
    """
    Apple ID belonging to the codesigning identity.
    """
    return "apple-codesign@artichokeruby.org"


def notarization_app_specific_password():
    """
    App-specific password for the notarization process belonging to the
    codesigning identity's Apple ID.
    """
    if app_specific_password := os.getenv("APPLE_ID_APP_PASSWORD"):
        return app_specific_password
    raise Exception("APPLE_ID_APP_PASSWORD environment variable is required")


def notarization_team_id():
    """
    Team ID belonging to the codesigning identity.
    """
    return "VDKP67932G"


def create_keychain(*, keychain_password):
    """
    Create a new keychain for the codesigning and notarization process.

    This ephemeral keychain stores Apple ID credentials for `notarytool` and
    code signing certificates for `codesign`.
    """

    # Ensure keychain does not exist.
    delete_keychain()

    with log_group("Setup notarization keychain"):
        # security create-keychain -p "$keychain_password" "$keychain_path"
        subprocess.run(
            [
                "security",
                "create-keychain",
                "-p",
                keychain_password,
                str(keychain_path()),
            ],
            check=True,
        )
        # security set-keychain-settings -lut 900 "$keychain_path"
        subprocess.run(
            [
                "security",
                "set-keychain-settings",
                "-lut",
                "900",
                str(keychain_path()),
            ],
            check=True,
        )
        # security unlock-keychain -p "$keychain_password" "$keychain_path"
        subprocess.run(
            [
                "security",
                "unlock-keychain",
                "-p",
                keychain_password,
                str(keychain_path()),
            ],
            check=True,
        )


def delete_keychain():
    """
    Delete the keychain for the codesigning and notarization process.
    Create a new keychain for the codesigning and notarization process.

    This ephemeral keychain stores Apple ID credentials for `notarytool` and
    code signing certificates for `codesign`.
    """

    with log_group("Delete keychain"):
        try:
            # security delete-keychain /path/to/notarization.keychain-db
            subprocess.run(
                [
                    "security",
                    "delete-keychain",
                    str(keychain_path()),
                ],
                check=True,
            )
            print(f"Keychain deleted from {keychain_path()}")
        except subprocess.CalledProcessError as e:
            # keychain does not exist
            print(f"Keychain not found at {keychain_path()}, ignoring ...")


def import_notarization_credentials():
    """
    Import credentials required for notarytool to the codesigning and notarization
    process keychain.

    See `notarytool_credentials_profile`, `notarization_apple_id`,
    `notarization_app_specific_password`, and `notarization_team_id`.
    """

    with log_group("Import notarization credentials"):
        # xcrun notarytool store-credentials \
        #   "$notarytool_credentials_profile" \
        #   --apple-id "apple-codesign@artichokeruby.org" \
        #   --password "$APPLE_ID_APP_PASSWORD" \
        #   --team-id "VDKP67932G" \
        #   --keychain "$keychain_path"
        subprocess.run(
            [
                "/usr/bin/xcrun",
                "notarytool",
                "store-credentials",
                notarytool_credentials_profile(),
                "--apple-id",
                notarization_apple_id(),
                "--password",
                notarization_app_specific_password(),
                "--team-id",
                notarization_team_id(),
                "--keychain",
                str(keychain_path()),
            ],
            check=True,
        )


def import_codesigning_certificate():
    """
    Import codesigning certificate into the codesigning and notarization process
    keychain.

    The certificate is expected to be a base64-encoded string stored in the
    `MACOS_CERTIFICATE` environment variable with a password given by the
    `MACOS_CERTIFICATE_PWD` environment variable.

    The base64-encoded certificate is stored in a temporary file so it may be
    imported into the keychain by the `security` utility.
    """

    with log_group("Import codesigning certificate"):
        encoded_certificate = os.getenv("MACOS_CERTIFICATE")
        if not encoded_certificate:
            raise Exception("MACOS_CERTIFICATE environment variable is required")

        try:
            certificate = base64.b64decode(encoded_certificate, validate=True)
        except binascii.Error:
            raise Exception("MACOS_CERTIFICATE must be base64 encoded")

        certificate_password = os.getenv("MACOS_CERTIFICATE_PWD")
        if not certificate_password:
            raise Exception(
                "MACOS_CERTIFICATE_PASSWORD environment variable is required"
            )

        with tempfile.TemporaryDirectory() as tempdirname:
            cert = Path(tempdirname).joinpath("certificate.p12")
            cert.write_bytes(certificate)
            # security import certificate.p12 -k "$keychain_path" -P "$MACOS_CERTIFICATE_PWD" -T /usr/bin/codesign
            subprocess.run(
                [
                    "security",
                    "import",
                    str(cert),
                    "-k",
                    str(keychain_path()),
                    "-P",
                    certificate_password,
                    "-T",
                    "/usr/bin/codesign",
                ],
                check=True,
            )


def setup_codesigning_and_notarization_keychain(*, keychain_password):
    """
    Create and prepare a keychain for the codesigning and notarization process.

    A new keychain with the given password is created and set to be ephemeral.
    Notarization credentials and codesigning certificates are imported into the
    keychain.
    """

    create_keychain(keychain_password=keychain_password)
    import_notarization_credentials()
    import_codesigning_certificate()

    with log_group("Prepare keychain for codesigning"):
        # security set-key-partition-list -S "apple-tool:,apple:,codesign:" -s -k "$keychain_password" "$keychain_path"
        subprocess.run(
            [
                "security",
                "set-key-partition-list",
                "-S",
                "apple-tool:,apple:,codesign:",
                "-s",
                "-k",
                keychain_password,
                str(keychain_path()),
            ],
            check=True,
        )


def codesign_binary(*, binary_path):
    """
    Run the codesigning process on the given binary.
    """
    # /usr/bin/codesign \
    #   --keychain "$keychain_path" \
    #   --sign "Developer ID Application: Ryan Lopopolo (VDKP67932G)" \
    #   --options runtime \
    #   --strict=all \
    #   --timestamp \
    #   --verbose \
    #   --force \
    #   "$binary_path"
    with log_group(f"Run codesigning [{binary_path.name}]"):
        subprocess.run(
            [
                "/usr/bin/codesign",
                "--keychain",
                str(keychain_path()),
                "--sign",
                codesigning_identity(),
                # enable hardend runtime: https://developer.apple.com/documentation/security/hardened_runtime
                "--options=runtime",
                "--strict=all",
                "--timestamp",
                "-vvv",
                "--force",
                str(binary_path),
            ],
            check=True,
        )


def create_notarization_bundle(*, release_name, binaries, resources):
    """
    Create a disk image with the codesigned binaries to submit to the Apple
    notarization service and prepare for distribution.

    Returns `Path` object to the newly created DMG archive.
    """

    with log_group("Create disk image for notarization"):
        dmg = Path(f"{release_name}.dmg")
        dmg.unlink(missing_ok=True)

        try:
            shutil.rmtree(release_name)
        except FileNotFoundError:
            pass
        os.makedirs(release_name, exist_ok=True)

        for binary in binaries:
            shutil.copy(binary, release_name)
        for resource in resources:
            shutil.copy(resource, release_name)

        # notarytool submit works only with UDIF disk images, signed "flat"
        # installer packages, and zip files.
        #
        # Format types:
        #
        # UDZO - UDIF zlib-compressed image
        # ULFO - UDIF lzfse-compressed image (OS X 10.11+ only)
        # ULMO - UDIF lzma-compressed image (macOS 10.15+ only)

        # /usr/bin/hdiutil create \
        #    -volname "Artichoke Ruby nightly" \
        #    -srcfolder "$release_name" \
        #    -ov -format UDZO name.dmg
        subprocess.run(
            [
                "/usr/bin/hdiutil",
                "create",
                "-volname",
                "Artichoke Ruby nightly",
                "-srcfolder",
                release_name,
                "-ov",
                "-format",
                "UDZO",
                "-verbose",
                str(dmg),
            ],
            check=True,
        )
        codesign_binary(binary_path=dmg)
        return dmg


def notarize_bundle(*, bundle):
    """
    Submit the bundle to Apple for notarization using notarytool.

    This method will block until the notarization process is complete.

    https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution/customizing_the_notarization_workflow
    """

    notarization_request = None

    # xcrun notarytool submit "$bundle_name" \
    #   --keychain-profile "$notarytool_credentials_profile" \
    #   --keychain "$keychain_path" \
    #   --wait
    with log_group("Notarize disk image"):
        proc = subprocess.run(
            [
                "/usr/bin/xcrun",
                "notarytool",
                "submit",
                bundle,
                "--keychain-profile",
                notarytool_credentials_profile(),
                "--keychain",
                str(keychain_path()),
                "--wait",
            ],
            check=True,
            capture_output=True,
            encoding="utf8",
        )
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        for line in proc.stdout.splitlines():
            print(line.rstrip())
            line = line.strip()
            if line.startswith("id: "):
                notarization_request = line.removeprefix("id: ")

    if not notarization_request:
        raise Exception("Notarization request did not return an id on success")

    # xcrun notarytool log 2efe2717-52ef-43a5-96dc-0797e4ca1041 --keychain-profile "AC_PASSWORD" developer_log.json
    with log_group("Fetch notarization logs"):
        with tempfile.TemporaryDirectory() as tempdirname:
            logs = Path(tempdirname).joinpath("notarization_logs.json")
            subprocess.run(
                [
                    "/usr/bin/xcrun",
                    "notarytool",
                    "log",
                    notarization_request,
                    "--keychain-profile",
                    notarytool_credentials_profile(),
                    "--keychain",
                    str(keychain_path()),
                    str(logs),
                ],
                check=True,
            )
            with logs.open("r") as log:
                log_json = json.load(log)
                print(json.dumps(log_json, indent=4))


def staple_bundle(*, bundle):
    """
    Staple the diskimage with `stapler`.
    """

    with log_group("Staple disk image"):
        subprocess.run(
            [
                "/usr/bin/xcrun",
                "stapler",
                "staple",
                "-v",
                str(bundle),
            ],
            check=True,
        )


def validate(*, bundle, binary_names):
    """
    Verify the stapled disk image and codesigning of binaries within it.
    """
    with log_group("Verify disk image staple"):
        subprocess.run(
            [
                "/usr/bin/xcrun",
                "stapler",
                "validate",
                "-v",
                str(bundle),
            ],
            check=True,
        )

    with log_group("Verify disk image signature"):
        # spctl -a -t open --context context:primary-signature 2022-09-03-test-codesign-notarize-dmg-v1.dmg -v
        subprocess.run(
            [
                "/usr/sbin/spctl",
                "-a",
                "-t",
                "open",
                "--context",
                "context:primary-signature",
                str(bundle),
                "-v",
            ],
            check=True,
        )

    with attach_disk_image(bundle) as mounted_image:
        for binary in binary_names:
            mounted_binary = mounted_image.joinpath(binary)
            with log_group(f"Verify signature: {binary}"):
                subprocess.run(
                    [
                        "/usr/bin/codesign",
                        "--verify",
                        "--check-notarization",
                        "--deep",
                        "--strict=all",
                        "-vvv",
                        str(mounted_binary),
                    ],
                    check=True,
                )

            with log_group(f"Display signature: {binary}"):
                subprocess.run(
                    [
                        "/usr/bin/codesign",
                        "--display",
                        "--check-notarization",
                        "-vvv",
                        str(mounted_binary),
                    ],
                    check=True,
                )


def main(args):
    if not args:
        print("Error: pass binaries to sign as positional arguments", file=sys.stderr)
        return 1

    binaries = []
    resources = []
    append_next = None
    for arg in args:
        if append_next is None:
            if arg == "--binary":
                append_next = binaries
                continue
            if arg == "--resource":
                append_next = resources
                continue
            print(f"Unexpected argument: {arg}", file=sys.stderr)
        append_next.append(Path(arg))
        append_next = None

    for binary in binaries:
        if not binary.is_file():
            print("Error: {binary} does not exist", file=sys.stderr)
            return 1

    try:
        keychain_password = secrets.token_urlsafe()
        setup_codesigning_and_notarization_keychain(keychain_password=keychain_password)

        for binary in binaries:
            codesign_binary(binary_path=binary)

        bundle = create_notarization_bundle(
            release_name="2022-09-03-test-codesign-notarize-dmg-v1",
            binaries=binaries,
            resources=resources,
        )
        notarize_bundle(bundle=bundle)
        staple_bundle(bundle=bundle)
        validate(bundle=bundle, binary_names=[binary.name for binary in binaries])
        return 0
    except subprocess.CalledProcessError as e:
        print(
            f"Error: failed to invoke command.\n\tCommand: {e.cmd}\n\tReturn Code: {e.returncode}",
            file=sys.stderr,
        )
        return e.returncode
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(traceback.format_exc())
        return 1
    finally:
        # Purge keychain.
        delete_keychain()


if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(main(args))
