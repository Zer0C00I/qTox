# Install Instructions

- [Dependencies](#dependencies)
- [Linux](#linux)
  - [Debian / Ubuntu](#debian--ubuntu)
  - [Fedora](#fedora)
  - [Arch Linux](#arch-linux)
  - [Other distributions](#other-distributions)
- [FreeBSD](#freebsd)
- [macOS](#macos)
- [Compile-time switches](#compile-time-switches)
- [CMake presets](#cmake-presets)

---

## Dependencies

### Required

| Name         | Version    | Notes                                      |
|--------------|------------|--------------------------------------------|
| C++ compiler | clang++ ≥ 20 (recommended) or GCC ≥ 13 | C++23 required |
| [CMake]      | ≥ 3.19     | For preset support                         |
| [Ninja]      | any        |                                            |
| [lld]        | ≥ 20       | Required for Thin LTO with clang           |
| [Qt]         | ≥ 6.2      | modules: core, gui, network, svg, widgets, xml, concurrent |
| [toxcore]    | ≥ 0.2.20   | libtoxcore + libtoxav                      |
| [FFmpeg]     | ≥ 4.4      | avcodec, avdevice, avformat, avutil, swscale |
| [OpenAL Soft]| ≥ 1.16     |                                            |
| [opus]       | ≥ 1.0      |                                            |
| [libvpx]     | ≥ 1.6      |                                            |
| [libexif]    | ≥ 0.6      |                                            |
| [qrencode]   | ≥ 3.0      |                                            |
| [sqlcipher]  | ≥ 3.2      |                                            |
| [libsodium]  | ≥ 1.0      |                                            |
| [pkg-config] | any        |                                            |

### Optional

| Name           | CMake flag         | Notes                        |
|----------------|--------------------|------------------------------|
| [KSonnet]      | `-DSPELL_CHECK=ON` | Spell checking (default: ON) |
| [libXScrnSaver]| auto-detected      | Auto-away on X11             |
| [libX11]       | auto-detected      | Auto-away on X11             |

---

## Linux

### Clone the repository

```bash
git clone --recursive https://github.com/Zer0C00I/qTox.git
cd qTox
```

### Build toxcore

toxcore is not yet available in most distribution repositories at the required
version. Build it from source:

```bash
git clone --depth=1 --recursive https://github.com/TokTok/c-toxcore.git toxcore
cmake -S toxcore -B toxcore/_build -GNinja -DBOOTSTRAP_DAEMON=OFF
cmake --build toxcore/_build
sudo cmake --install toxcore/_build
sudo ldconfig
```

### Debian / Ubuntu

Install clang-20 from the upstream LLVM repository (required for Thin LTO):

```bash
wget -qO /tmp/llvm.sh https://apt.llvm.org/llvm.sh
chmod +x /tmp/llvm.sh
echo "" | sudo /tmp/llvm.sh 20
sudo apt-get install -y clang-20 clang-tidy-20 lld-20
sudo update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-20 100
sudo update-alternatives --install /usr/bin/ld ld /usr/bin/ld.lld-20 100
```

Install build dependencies:

```bash
sudo apt-get update
sudo apt-get install -y \
  cmake ninja-build pkg-config \
  libavcodec-dev libavdevice-dev libavformat-dev libavutil-dev libswscale-dev \
  libexif-dev libopenal-dev libopus-dev libvpx-dev \
  libqrencode-dev libsodium-dev libsqlcipher-dev \
  libgl-dev libv4l-dev libxss-dev libunwind-dev \
  qt6-base-dev qt6-svg-dev qt6-tools-dev qt6-tools-dev-tools qt6-l10n-tools
```

Build:

```bash
cmake --preset clang-strict
cmake --build --preset clang-strict
```

Binary is in `_build_clang_strict/qtox`.

### Fedora

Install build dependencies:

```bash
sudo dnf install -y \
  cmake ninja-build pkgconf-pkg-config \
  clang lld gcc-c++ \
  ffmpeg-devel \
  openal-soft-devel opus-devel libvpx-devel \
  libexif-devel libqrencode-devel libsodium-devel sqlcipher-devel \
  libv4l-devel libXScrnSaver-devel mesa-libGL-devel \
  qt6-qtbase-devel qt6-qtsvg-devel qt6-qttools-devel
```

Build:

```bash
cmake --preset clang-strict
cmake --build --preset clang-strict
```

### Arch Linux

Install build dependencies:

```bash
sudo pacman -S --needed \
  cmake ninja pkgconf \
  clang lld gcc \
  ffmpeg openal opus libvpx \
  libexif qrencode libsodium sqlcipher \
  v4l-utils libxss \
  qt6-base qt6-svg qt6-tools
```

toxcore is available in the AUR:

```bash
# with your AUR helper, e.g.:
yay -S toxcore
```

Build:

```bash
cmake --preset clang-strict
cmake --build --preset clang-strict
```

### Other distributions

Install the equivalent packages for your distribution. Then:

```bash
cmake -S . -B _build -GNinja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_COMPILER=clang++
cmake --build _build
```

---

## FreeBSD

Pre-built `.pkg` packages are available as CI artifacts on the
[Releases](https://github.com/Zer0C00I/qTox/releases) page.

To install a downloaded package:

```sh
pkg install ./qtox-*.pkg
```

To build from source:

```sh
pkg upgrade
pkg install -y \
  cmake ninja pkgconf \
  qt6-base qt6-tools qt6-svg \
  openal-soft opus libvpx v4l_compat libexif libqrencode \
  libsodium sqlcipher ffmpeg toxcore llvm

git clone --recursive https://github.com/Zer0C00I/qTox.git
cd qTox
cmake -S . -B _build -GNinja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_COMPILER=clang++
cmake --build _build
```

---

## macOS

Requires macOS ≥ 12 and [Homebrew](https://brew.sh).

Install dependencies:

```bash
brew install cmake ninja pkg-config \
  qt@6 ffmpeg openal-soft opus libvpx \
  libexif qrencode libsodium sqlcipher
```

Build toxcore:

```bash
git clone --depth=1 --recursive https://github.com/TokTok/c-toxcore.git toxcore
cmake -S toxcore -B toxcore/_build -GNinja -DBOOTSTRAP_DAEMON=OFF
cmake --build toxcore/_build
sudo cmake --install toxcore/_build
```

Build qTox:

```bash
cmake -S . -B _build -GNinja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_PREFIX_PATH="$(brew --prefix qt@6)"
cmake --build _build
```

---

## Compile-time switches

Pass as `-DSWITCH=ON/OFF` to `cmake`. Key options:

| Switch           | Default | Description                              |
|------------------|---------|------------------------------------------|
| `STRICT_OPTIONS` | OFF     | Treat all warnings as errors (`-Werror`) |
| `SPELL_CHECK`    | ON      | KSonnet spell checking                   |
| `UPDATE_CHECK`   | ON      | Check for new versions at startup        |
| `BUILD_TESTING`  | ON      | Build unit tests                         |

---

## CMake presets

| Preset          | Compiler | Description                                       |
|-----------------|----------|---------------------------------------------------|
| `clang-strict`  | clang++  | `-Werror`, all security flags, Thin LTO, `-O3` (recommended) |
| `asan`          | clang++  | Debug + ASan + UBSan (integer, nullability, local-bounds) |
| `dev`           | system   | Debug build, no strict warnings                   |
| `release`       | system   | RelWithDebInfo build                              |
| `tsan`          | system   | Debug + TSan                                      |

Usage:

```bash
cmake --preset <name>
cmake --build --preset <name>
```

Binary output directories: `_build_clang_strict/`, `_build-asan/`, `_build/`, etc.

[CMake]: https://cmake.org/
[FFmpeg]: https://www.ffmpeg.org/
[KSonnet]: https://github.com/KDE/sonnet
[libexif]: https://libexif.github.io/
[libsodium]: https://libsodium.gitbook.io/
[libX11]: https://www.x.org/wiki/
[libXScrnSaver]: https://www.x.org/wiki/Releases/ModuleVersions/
[lld]: https://lld.llvm.org/
[Ninja]: https://ninja-build.org/
[OpenAL Soft]: https://openal-soft.org/
[opus]: https://opus-codec.org/
[pkg-config]: https://www.freedesktop.org/wiki/Software/pkg-config/
[qrencode]: https://fukuchi.org/works/qrencode/
[Qt]: https://www.qt.io/
[sqlcipher]: https://www.zetetic.net/sqlcipher/
[toxcore]: https://github.com/TokTok/c-toxcore/
[libvpx]: https://www.webmproject.org/code/
