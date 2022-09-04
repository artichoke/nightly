#!/usr/bin/env bash

set -x
set -euo pipefail

setup_notarization_keychain() {
  local -r keychain_path="$1"
  local -r notarytool_credentials_profile="$2"
  local -r keychain_password="$(uuidgen)"

  echo "::group::setup keychain"
  security create-keychain -p "$keychain_password" "$keychain_path"
  security set-keychain-settings -lut 900 "$keychain_path"
  security unlock-keychain -p "$keychain_password" "$keychain_path"
  echo "::endgroup::"

  echo "::group::import notarization credentials"
  xcrun notarytool store-credentials \
    "$notarytool_credentials_profile" \
    --apple-id "apple-codesign@artichokeruby.org" \
    --password "$APPLE_ID_APP_PASSWORD" \
    --team-id "VDKP67932G" \
    --keychain "$keychain_path"
  echo "::endgroup::"

  echo "::group::import signing certificate"
  printenv MACOS_CERTIFICATE | base64 --decode > certificate.p12
  security import certificate.p12 -k "$keychain_path" -P "$MACOS_CERTIFICATE_PWD" -T /usr/bin/codesign
  shred --random=/dev/urandom -z -u certificate.p12
  echo "::endgroup::"

  echo "::group::prepare keychain for codesigning"
  security set-key-partition-list -S "apple-tool:,apple:,codesign:" -s -k "$keychain_password" "$keychain_path"
  echo "::endgroup::"
}

codesign_binary() {
  local -r section="$1"
  local -r binary_path="$2"
  local -r keychain_path="$3"

  echo "::group::codesign -- $section"
  # enable hardend runtime: https://developer.apple.com/documentation/security/hardened_runtime
  /usr/bin/codesign \
    --keychain "$keychain_path" \
    --sign "Developer ID Application: Ryan Lopopolo (VDKP67932G)" \
    --options runtime \
    --strict=all \
    --timestamp \
    --verbose \
    --force \
    "$binary_path"
  echo "::endgroup::"

  echo "::group::verify codesigning - $section"
  /usr/bin/codesign --verify -vvv "$binary_path"
  echo "::endgroup::"

  echo "::group::display code signature - $section"
  /usr/bin/codesign --display -vvv "$binary_path"
  echo "::endgroup::"
}

create_notarization_bundle() {
  local -r release_name="$1"
  local -r bundle_name="${release_name}.zip"
  shift

  rm -rf "$release_name" "$bundle_name"
  mkdir "$release_name"

  cp -v "$@" "$release_name"
  /usr/bin/hdiutil create \
    -volname "Artichoke Ruby nightly" \
    -srcfolder "$release_name" \
    -ov -format UDZO name.dmg
  /usr/bin/ditto -c -k --keepParent "nightly-test-codesign-2022-09-03" "$bundle_name"

  echo "$bundle_name"
}

notarize_binaries() {
  local -r keychain_path="$1"
  local -r notarytool_credentials_profile="$2"
  local -r bundle_name="$3"

  echo "::group::notarizing bundle"
  xcrun notarytool submit "$bundle_name" \
    --keychain-profile "$notarytool_credentials_profile" \
    --keychain "$keychain_path" \
    --wait
  echo "::endgroup::"
}

cleanup() {
  local -r keychain_path="$1"

  echo "::group::deleting keychain"
  security delete-keychain "$keychain_path"
  echo "::endgroup::"
}

main() {
  local -r notarization_keychain_path="$(pwd)/notarization.keychain-db"
  local -r notarytool_keychain_profile="artichoke-apple-codesign-notarize"

  setup_notarization_keychain "$notarization_keychain_path" "$notarytool_keychain_profile"

  codesign_binary "artichoke" "../artichoke/target/release/artichoke" "$notarization_keychain_path"
  codesign_binary "airb" "../artichoke/target/release/airb" "$notarization_keychain_path"

  local -r assets=(
    "../artichoke/target/release/artichoke"
    "../artichoke/target/release/airb"
    "../artichoke/LICENSE"
    "../artichoke/README.md"
  )

  echo "::group::creating notarization zip bundle"
  local -r notarization_bundle="$(create_notarization_bundle "codesign-test-2022-09-03-v1" "${assets[@]}")"
  echo "::endgroup::"

  notarize_binaries "$notarization_keychain_path" "$notarytool_keychain_profile" "$notarization_bundle"

  cleanup
}

main
