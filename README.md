# Artichoke Nightly Builds

[![GitHub Actions](https://github.com/artichoke/nightly/workflows/CI/badge.svg)](https://github.com/artichoke/nightly/actions)
[![Discord](https://img.shields.io/discord/607683947496734760)](https://discord.gg/QCe2tp2)
[![Twitter](https://img.shields.io/twitter/follow/artichokeruby?label=Follow&style=social)](https://twitter.com/artichokeruby)

Nightly builds of [Artichoke Ruby].

Docker images for nightly builds are built at
[artichoke/docker-artichoke-nightly][docker-nightly].

[Install the latest nightly build of Artichoke][nightly-releases].

## Install

Nightly builds are distributed with [`ruby-build`].

To install with `ruby-build`:

```shell
$ ruby-build artichoke-dev ~/.rubies/artichoke
```

Or with `rbenv`:

```shell
$ rbenv install artichoke-dev
```

## Platforms

Currently supported nightly targets are:

- `x86_64-unknown-linux-gnu`
- `x86_64-unknown-linux-musl`
- `x86_64-apple-darwin`
- `x86_64-pc-windows-msvc`
- `aarch64-apple-darwin` (Apple Silicon)

## Code Signing

Release artifacts are signed with the the following GPG key:

**User ID**: Code signing for Artichoke Ruby \<codesign@artichokeruby.org\>  
**Signing Key ID**: AF57A37CAC061452  
**Signing Key Fingerprint**: 1C4A856ACF86EC1EE841180FAF57A37CAC061452  
**Public Key**: <https://github.com/artichoke-ci.gpg>, [artichoke/nightly#20],
[artichoke/nightly@84e687e866edb52a43a4f462accf3020fe8797f1].

[artichoke ruby]: https://github.com/artichoke/artichoke
[docker-nightly]: https://github.com/artichoke/docker-artichoke-nightly
[nightly-releases]: https://github.com/artichoke/nightly/releases
[`ruby-build`]: https://github.com/rbenv/ruby-build
[artichoke/nightly#20]: https://github.com/artichoke/nightly/pull/20
[artichoke/nightly@84e687e866edb52a43a4f462accf3020fe8797f1]:
  https://github.com/artichoke/nightly/commit/84e687e866edb52a43a4f462accf3020fe8797f1
