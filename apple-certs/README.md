# Apple Certificates

Several certificates are required by the build keychain used in the codesigning
process.

## Certificate Chain

The build keychain must include the all intermediate certificates for the
codesigning certificate.

All of Apple's CAs can be found at:
<https://www.apple.com/certificateauthority/>.

The Developer ID Application certificate used for codesigning has "Developer
ID - G2 (Expiring 09/17/2031 00:00:00 UTC)" as an intermediate in its
certificate chain.

The root certificate in the chain is

## Provisioning Profile

`artichoke-provisioning-profile-signing.cer` contains a provisioning profile
which is associated with the Developer ID application and is required for
signing.
