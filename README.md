<div align="center">

# DroidBridge

### Native Linux Android USB screen mirroring and audio forwarding

Mirror your Android phone screen to Linux over USB, with audio.
Built with Python 3, GTK 4, libadwaita, ADB, and scrcpy.

<br />

[![Stars](https://img.shields.io/github/stars/ankitkhatrik6/DroidBridge?style=flat-square&logo=github&logoColor=white&color=FFC107&labelColor=1A1A1A)](https://github.com/ankitkhatrik6/DroidBridge/stargazers)
[![Forks](https://img.shields.io/github/forks/ankitkhatrik6/DroidBridge?style=flat-square&logo=github&logoColor=white&color=0969DA&labelColor=1A1A1A)](https://github.com/ankitkhatrik6/DroidBridge/network/members)
[![Issues](https://img.shields.io/github/issues/ankitkhatrik6/DroidBridge?style=flat-square&logo=github&logoColor=white&color=E53935&labelColor=1A1A1A)](https://github.com/ankitkhatrik6/DroidBridge/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/ankitkhatrik6/DroidBridge?style=flat-square&logo=github&logoColor=white&color=2EA043&labelColor=1A1A1A)](https://github.com/ankitkhatrik6/DroidBridge/pulls)
[![Last Commit](https://img.shields.io/github/last-commit/ankitkhatrik6/DroidBridge?style=flat-square&logo=github&logoColor=white&color=8E24AA&labelColor=1A1A1A)](https://github.com/ankitkhatrik6/DroidBridge/commits/main)
[![License](https://img.shields.io/badge/License-Apache_2.0-D32F2F?style=flat-square&logo=apache&logoColor=white&labelColor=1A1A1A)](LICENSE)

<br />

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](#tech-stack)
[![GTK](https://img.shields.io/badge/GTK-4.0-4A86CF?style=flat-square&logo=gnome&logoColor=white)](#tech-stack)
[![scrcpy](https://img.shields.io/badge/scrcpy-2.0+-00C853?style=flat-square&logo=android&logoColor=white)](#tech-stack)
[![ADB](https://img.shields.io/badge/ADB-1.0.41-FF9800?style=flat-square&logo=androidstudio&logoColor=white)](#tech-stack)
[![Linux](https://img.shields.io/badge/Linux-Ubuntu_|_Debian_|_Lubuntu-E95420?style=flat-square&logo=linux&logoColor=white)](#installation)

<br />

[Installation](#installation) &nbsp;|&nbsp; [Features](#features) &nbsp;|&nbsp; [Usage](#usage) &nbsp;|&nbsp; [Tech Stack](#tech-stack) &nbsp;|&nbsp; [Contributing](#contributing)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Android Device Setup](#android-device-setup)
- [Usage](#usage)
- [Tech Stack](#tech-stack)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Overview

DroidBridge mirrors an Android phone's screen to a Linux desktop over USB, with internal phone audio forwarded to PC speakers. It ships as a native GTK 4 application with no cloud component, no account, and no network dependency beyond the USB connection.

## Features

| Feature | Description |
|---------|-------------|
| **Native Linux desktop UI** | GTK 4 with libadwaita, falling back to pure GTK 4 on lightweight desktop environments (Lubuntu, XFCE, LXQt). |
| **Low-latency screen mirroring** | Resizable native window with 1080p, 720p, 4K, or native resolution. |
| **USB audio forwarding** | Internal phone audio forwarded to PC speakers (Android 11+, scrcpy 2.0+). |
| **Preset system** | 1080p Balanced, 720p Low Latency, and 4K High Quality presets. |
| **Process supervision** | GLib async process management with clean subprocess reaping. |
| **Real-time diagnostics** | One-click environment check with a redacted report export. |
| **XDG compliant** | Config stored in `~/.config/droidbridge/`, logs in `~/.local/state/droidbridge/`. |

## Installation

### Debian Package (.deb)

```bash
# 1. Build the package
bash ./packaging/build_deb.sh

# 2. Install with APT (resolves dependencies automatically)
sudo apt install ./dist-deb/droidbridge_1.0.0-1_all.deb

# 3. Verify
droidbridge --version
droidbridge --diagnostics
```

### From Source

```bash
git clone https://github.com/ankitkhatrik6/DroidBridge.git
cd DroidBridge
bash ./packaging/build_deb.sh
sudo apt install ./dist-deb/droidbridge_1.0.0-1_all.deb
```

## Android Device Setup

| Step | Action |
|------|--------|
| 1 | **Developer Options** — Settings > About Phone > tap Build Number seven times. |
| 2 | **USB Debugging** — Settings > System > Developer Options > enable USB Debugging. |
| 3 | **Connect** — plug in with a data-capable USB cable. |
| 4 | **Authorize** — tap "Always allow from this computer" on the phone. |

> [!TIP]
> Use a data-capable USB cable, not just a charging cable.

## Usage

```bash
# Launch GUI
droidbridge

# Run diagnostics
droidbridge --diagnostics

# List connected devices
droidbridge --list-devices

# Target specific device
droidbridge -s <serial>

# Show version
droidbridge --version
```

## Tech Stack

| Area | Choice |
|------|--------|
| Language | Python 3.9+ |
| UI toolkit | GTK 4, libadwaita |
| Mirroring engine | scrcpy 2.0+ |
| Device bridge | ADB 1.0.41 |
| Packaging | Debian 12 / Ubuntu 24.04 `.deb` |

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/GTK-4-4A86CF?style=flat-square&logo=gnome&logoColor=white"/>
  <img src="https://img.shields.io/badge/libadwaita-8957E5?style=flat-square&logo=gnome&logoColor=white"/>
  <img src="https://img.shields.io/badge/scrcpy-2.0+-00C853?style=flat-square&logo=android&logoColor=white"/>
  <img src="https://img.shields.io/badge/ADB-1.0.41-FF9800?style=flat-square&logo=androidstudio&logoColor=white"/>
  <img src="https://img.shields.io/badge/Debian_12-A80030?style=flat-square&logo=debian&logoColor=white"/>
  <img src="https://img.shields.io/badge/Ubuntu_24.04-E95420?style=flat-square&logo=ubuntu&logoColor=white"/>
</p>

## Testing

```bash
# Run unit tests
PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Contributing

Contributions are welcome. Please read the [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository.
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request.

## License

Distributed under the Apache License 2.0. See [LICENSE](LICENSE) for the full text.

## Author

Designed and developed by **Ankit**, a BSc CSIT student and full-stack developer based in Kathmandu, Nepal.

[![GitHub](https://img.shields.io/badge/GitHub-ankitkhatrik6-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/ankitkhatrik6)
[![Portfolio](https://img.shields.io/badge/Portfolio-ankitkhatri.me-FF6D00?style=flat-square&logo=googlechrome&logoColor=white)](https://ankitkhatri.me)
[![Instagram](https://img.shields.io/badge/Instagram-21ank1t-E4405F?style=flat-square&logo=instagram&logoColor=white)](https://instagram.com/21ank1t)

---

<div align="center">

If DroidBridge is useful to you, consider starring the repository.

</div>
