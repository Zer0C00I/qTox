# qTox

qTox is an instant messaging client using the encrypted peer-to-peer
[Tox](https://tox.chat) protocol. It supports text chat, file transfers, audio
calls, video calls, and conferences.

This repository is a fork of [TokTok/qTox](https://github.com/TokTok/qTox)
focused on **security hardening** and **performance**: eliminating undefined
behavior, tightening compiler warnings, enforcing strict build flags, and
reducing the attack surface of the application.

## Security hardening

All builds (not just CI) include:

| Category | Flags |
|---|---|
| Stack protection | `-fstack-protector-all`, `-fstack-clash-protection` |
| Control flow | `-fcf-protection=full` (x86), `-fno-plt` |
| Linker hardening | `-Wl,-z,relro`, `-Wl,-z,now`, `-Wl,-z,noexecstack`, `-Wl,-z,nodlopen` |
| Fortify | `-D_FORTIFY_SOURCE=3` (release), `-D_GLIBCXX_ASSERTIONS` (debug) |
| Sanitizers (CI) | ASan + UBSan including integer, nullability, local-bounds |

Warnings treated as errors in CI (`-Werror`). Only correctness and
security-relevant warnings are enabled — style warnings are excluded.

## Performance

Release builds (`RelWithDebInfo`, `Release`) use:

- **`-O3`** — auto-vectorization, aggressive inlining, loop optimizations
- **Thin LTO** (`-flto=thin` with lld) — whole-program optimization across
  translation units; typically 10–20% speedup and smaller binary
- C++23 standard

## CI

Three gate checks run on every push via clang-20 (installed from
[apt.llvm.org](https://apt.llvm.org)):

| Job | What it checks |
|---|---|
| `clang-strict` | Full build with `-Werror` and all security flags |
| `clang-tidy` | Static analysis with `WarningsAsErrors: '*'` |
| `ASan + UBSan` | Runtime sanitizer build + all 35 test suites |

Package jobs (DEB, RPM, AppImage, FreeBSD, macOS) only run after all
gate jobs pass.

## Supported platforms

| Platform | Package |
|---|---|
| Linux (Debian/Ubuntu) | `.deb` via CI artifacts |
| Linux (Fedora) | `.rpm` via CI artifacts |
| FreeBSD 14 | `.pkg` via CI artifacts |
| macOS (x86\_64, arm64) | `.dmg` via CI artifacts |

## Building

### Dependencies (Debian/Ubuntu)

```bash
sudo apt-get install -y clang lld cmake ninja-build \
  libavcodec-dev libavdevice-dev libavformat-dev libavutil-dev libswscale-dev \
  libexif-dev libopenal-dev libopus-dev libvpx-dev \
  libqrencode-dev libsodium-dev libsqlcipher-dev \
  libgl-dev libv4l-dev libxss-dev libunwind-dev \
  qt6-base-dev qt6-svg-dev qt6-tools-dev qt6-tools-dev-tools qt6-l10n-tools \
  pkg-config
```

### Build toxcore

```bash
git clone --depth=1 --recursive https://github.com/TokTok/c-toxcore.git toxcore
cmake -B toxcore/_build -S toxcore -GNinja -DBOOTSTRAP_DAEMON=OFF
cmake --build toxcore/_build
sudo cmake --install toxcore/_build
```

### Build qTox

```bash
# Recommended: full security + performance flags
cmake --preset clang-strict
cmake --build --preset clang-strict
# Binary: _build_clang_strict/qtox

# ASan + UBSan (for development/testing)
cmake --preset asan
cmake --build --preset asan
ctest --test-dir _build-asan --parallel $(nproc) --output-on-failure
```

### CMake presets

| Preset | Description |
|---|---|
| `clang-strict` | clang++, `-Werror`, all security and performance flags |
| `asan` | Debug + ASan + UBSan, all tests |
| `dev` | Debug build, no strict warnings |

For detailed platform-specific instructions see [docs/INSTALL.md](docs/INSTALL.md).

## Features

- One-to-one and conference text chat
- File transfers with image preview
- Audio and video calls, including conference calls
- History and faux offline messages
- Avatars and emoticons
- Translations in over 30 languages

## License

GPLv3+. See [LICENSE](LICENSE).
