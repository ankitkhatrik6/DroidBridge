<p align="center">
  <h1 align="center">📱 DroidBridge</h1>
  <p align="center">
    Native Linux Android USB Screen Mirroring & Audio Forwarding
  </p>
</p>

<p align="center">
  <a href="https://github.com/ankitkhatrik6/DroidBridge/stargazers"><img src="https://img.shields.io/github/stars/ankitkhatrik6/DroidBridge?style=for-the-badge&color=yellow" alt="GitHub stars"/></a>
  <a href="https://github.com/ankitkhatrik6/DroidBridge/network/members"><img src="https://img.shields.io/github/forks/ankitkhatrik6/DroidBridge?style=for-the-badge&color=blue" alt="GitHub forks"/></a>
  <a href="https://github.com/ankitkhatrik6/DroidBridge/issues"><img src="https://img.shields.io/github/issues/ankitkhatrik6/DroidBridge?style=for-the-badge&color=red" alt="GitHub issues"/></a>
  <a href="https://github.com/ankitkhatrik6/DroidBridge/pulls"><img src="https://img.shields.io/github/issues-pr/ankitkhatrik6/DroidBridge?style=for-the-badge&color=green" alt="GitHub pull requests"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache_2.0-blue?style=for-the-badge" alt="License"/></a>
  <a href="https://github.com/ankitkhatrik6/DroidBridge/commits/main"><img src="https://img.shields.io/github/last-commit/ankitkhatrik6/DroidBridge?style=for-the-badge&color=brightgreen" alt="Last commit"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/GTK-4.0-yellow?style=for-the-badge&logo=gnome&logoColor=white" alt="GTK 4"/>
  <img src="https://img.shields.io/badge/scrcpy-2.0+-green?style=for-the-badge" alt="scrcpy"/>
  <img src="https://img.shields.io/badge/ADB-1.0.41-orange?style=for-the-badge" alt="ADB"/>
  <img src="https://img.shields.io/badge/Linux-Ubuntu_Debian_Lubuntu-lightgrey?style=for-the-badge&logo=linux&logoColor=white" alt="Linux"/>
</p>

---

<p align="center">
  <b>🔗 Mirror your Android phone screen to Linux over USB — with audio.</b><br>
  Built with <b>Python 3</b>, <b>GTK 4</b>, <b>libadwaita</b>, <b>ADB</b>, and <b>scrcpy</b>.
</p>

---

## 🚀 Features

<details>
  <summary><b>Click to expand features</b></summary>

- 🖥️ **Native Linux Desktop UI** — GTK 4 with libadwaita, falls back to pure GTK 4 on lightweight DEs (Lubuntu, XFCE, LXQt)
- 📱 **Zero-Latency Screen Mirroring** — Resizable native window with 1080p, 720p, 4K, or Native resolution
- 🎧 **USB Audio Forwarding** — Internal phone audio to PC speakers (Android 11+, scrcpy 2.0+)
- ⚡ **Preset System** — 1080p Balanced, 720p Low Latency, 4K High Quality
- 🛡️ **Process Supervision** — GLib async process management, clean subprocess reaping
- 🔍 **Real-Time Diagnostics** — One-click environment check with redacted report export
- 📁 **XDG Compliant** — Config in `~/.config/droidbridge/`, logs in `~/.local/state/droidbridge/`

</details>

---

## 📦 Installation

### Debian Package (`.deb`)

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

---

## 📱 Android Device Setup

1. **Developer Options** — Settings → About Phone → Tap Build Number 7×
2. **USB Debugging** — Settings → System → Developer Options → Enable USB Debugging
3. **Connect** — Plug in with a data-capable USB cable
4. **Authorize** — Tap **"Always allow from this computer"** on your phone

---

## 🎯 Usage

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

---

## 🛠️ Tech Stack

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/GTK-4-5A5A5A?style=for-the-badge&logo=gnome&logoColor=white"/>
  <img src="https://img.shields.io/badge/libadwaita-4A4A4A?style=for-the-badge&logo=gnome&logoColor=white"/>
  <img src="https://img.shields.io/badge/scrcpy-2.0+-00C853?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/ADB-1.0.41-FF9800?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Debian_12-020066?style=for-the-badge&logo=debian&logoColor=white"/>
  <img src="https://img.shields.io/badge/Ubuntu_24.04-E95420?style=for-the-badge&logo=ubuntu&logoColor=white"/>
</p>

---

## 🧪 Testing

```bash
# Run unit tests
PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the Apache-2.0 License. See [`LICENSE`](LICENSE) for more information.

---

<p align="center">
  <b>Made with ❤️ by <a href="https://github.com/ankitkhatrik6">ankitkhatrik6</a></b>
</p>


> 💡 **Tip**: Use a data-capable USB cable, not just a charging cable.
