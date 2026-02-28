# qTox

qTox is an instant messaging client using the encrypted peer-to-peer
[Tox](https://tox.chat) protocol. It supports text chat, file transfers, audio
calls, video calls, and conferences.

This repository is a fork of [TokTok/qTox](https://github.com/TokTok/qTox)
focused primarily on **security hardening**: eliminating undefined behavior,
tightening compiler warnings, enforcing strict build flags, and reducing the
attack surface of the application.

## Security focus

- Builds with `-DSTRICT_OPTIONS=ON`, `-fno-plt`, `-Wl,-z,nodlopen`, and
  `-Wthread-safety-beta` by default via the `clang-strict` CMake preset.
- All warnings treated as errors (`-Werror` / `CMAKE_COMPILE_WARNING_AS_ERROR`).
- Continuous static analysis: CodeQL, clang-tidy, cppcheck, PVS-Studio.
- Address Sanitizer and Undefined Behavior Sanitizer run in CI.
- C++23; no legacy workarounds retained for their own sake.

## Supported platforms

| Platform | Package |
|----------|---------|
| Linux (Debian/Ubuntu) | `.deb` via CI artifacts |
| Linux (Fedora) | `.rpm` via CI artifacts |
| FreeBSD 14 | built with clang++ |
| macOS | universal binary via CI artifacts |

## Building

### Quick start (Linux, clang)

```bash
# Install dependencies (Debian/Ubuntu example)
sudo apt-get install -y clang cmake ninja-build \
  libavcodec-dev libavdevice-dev libavformat-dev libavutil-dev libswscale-dev \
  libexif-dev libopenal-dev libopus-dev libvpx-dev \
  libqrencode-dev libsodium-dev libsqlcipher-dev \
  libgl-dev libv4l-dev libxss-dev libunwind-dev \
  qt6-base-dev qt6-svg-dev qt6-tools-dev qt6-tools-dev-tools qt6-l10n-tools \
  pkg-config

# Build toxcore (if not available as a system package)
git clone --depth=1 --recursive https://github.com/TokTok/c-toxcore.git toxcore
cmake -B toxcore/_build -S toxcore -GNinja -DBOOTSTRAP_DAEMON=OFF
cmake --build toxcore/_build
sudo cmake --install toxcore/_build

# Build qTox with the clang-strict preset
cmake --preset clang-strict
cmake --build --preset clang-strict
```

The `clang-strict` preset produces the binary in `_build_clang_strict/`.

### CMake presets

| Preset | Description |
|--------|-------------|
| `clang-strict` | Clang, strict warnings, security hardening flags (recommended) |

See `CMakePresets.json` for full flag details.

### Manual build

```bash
cmake -S . -B _build -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_COMPILER=clang++
cmake --build _build -j$(nproc)
```

For detailed platform-specific instructions see [INSTALL.md](INSTALL.md).

## Features

- One-to-one and conference text chat
- File transfers with image preview
- Audio and video calls, including conference calls
- History and faux offline messages
- Avatars and emoticons
- Translations in over 30 languages

## License

GPLv3+. See [LICENSE](LICENSE).
