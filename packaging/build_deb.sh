#!/usr/bin/env bash
# ==============================================================================
# DroidBridge - Automated Debian Package (.deb) Builder
# Builds a standard Debian package compliant with Ubuntu 22.04/24.04 and Debian 12.
# ==============================================================================

set -euo pipefail

PACKAGE_NAME="droidbridge"
VERSION="1.0.0"
REVISION="1"
ARCH="all"
DEB_NAME="${PACKAGE_NAME}_${VERSION}-${REVISION}_${ARCH}.deb"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist-deb"
BUILD_DIR="${DIST_DIR}/staging"

echo "=== Building DroidBridge Debian Package: ${DEB_NAME} ==="
echo "Project Root: ${ROOT_DIR}"

# 1. Clean previous builds
rm -rf "${DIST_DIR}"
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/lib/droidbridge"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${BUILD_DIR}/usr/share/doc/droidbridge"

# 2. Copy Python application source files
echo "Installing application files into /usr/lib/droidbridge..."
mkdir -p "${BUILD_DIR}/usr/lib/droidbridge"
cp -r "${ROOT_DIR}/src/droidbridge" "${BUILD_DIR}/usr/lib/droidbridge/"
chmod -R 755 "${BUILD_DIR}/usr/lib/droidbridge"
find "${BUILD_DIR}/usr/lib/droidbridge" -name "*.py" -exec chmod 644 {} +
find "${BUILD_DIR}/usr/lib/droidbridge" -name "*.css" -exec chmod 644 {} +

# 3. Create /usr/bin/droidbridge executable launcher wrapper
echo "Generating launcher wrapper in /usr/bin/droidbridge..."
cat << 'EOF' > "${BUILD_DIR}/usr/bin/droidbridge"
#!/usr/bin/env bash
# DroidBridge system launcher wrapper
export PYTHONPATH="/usr/lib/droidbridge:${PYTHONPATH:-}"
exec /usr/bin/python3 -m droidbridge.main "$@"
EOF
chmod 755 "${BUILD_DIR}/usr/bin/droidbridge"

# 4. Copy FreeDesktop desktop entry and icons
echo "Installing desktop launcher and icon assets..."
cp "${ROOT_DIR}/data/org.droidbridge.DroidBridge.desktop" "${BUILD_DIR}/usr/share/applications/"
chmod 644 "${BUILD_DIR}/usr/share/applications/org.droidbridge.DroidBridge.desktop"

cp "${ROOT_DIR}/data/icons/scalable/apps/org.droidbridge.DroidBridge.svg" "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/"
chmod 644 "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/org.droidbridge.DroidBridge.svg"

# 5. Documentation and copyright
echo "Installing copyright and changelog..."
if [ -f "${ROOT_DIR}/LICENSE" ]; then
    cp "${ROOT_DIR}/LICENSE" "${BUILD_DIR}/usr/share/doc/droidbridge/copyright"
fi
gzip -9cn "${ROOT_DIR}/packaging/debian/changelog" > "${BUILD_DIR}/usr/share/doc/droidbridge/changelog.Debian.gz"
chmod 644 "${BUILD_DIR}/usr/share/doc/droidbridge/"*

# 6. Copy Debian package control metadata and maintainer scripts
echo "Configuring Debian control metadata..."
cat << EOF > "${BUILD_DIR}/DEBIAN/control"
Package: ${PACKAGE_NAME}
Version: ${VERSION}-${REVISION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: DroidBridge Maintainers <packages@droidbridge.org>
Depends: python3 (>= 3.9), python3-gi, gir1.2-gtk-4.0, adb | android-tools-adb
Recommends: gir1.2-adw-1, pipewire-pulse | pulseaudio, scrcpy (>= 2.0)
Homepage: https://github.com/droidbridge/droidbridge
Description: Native Linux Android USB screen mirroring and audio forwarding
 DroidBridge is a native Linux desktop application that connects to Android
 phones over a USB data cable, mirrors the phone display in a separate native
 desktop window, and forwards phone audio to the computer sound system.
 .
 Built with Python 3, GTK 4, libadwaita, ADB, and scrcpy. Supports Ubuntu
 22.04 LTS, Ubuntu 24.04 LTS, Debian 12 Bookworm, and Lubuntu.
EOF

cp "${ROOT_DIR}/packaging/debian/postinst" "${BUILD_DIR}/DEBIAN/postinst"
cp "${ROOT_DIR}/packaging/debian/postrm" "${BUILD_DIR}/DEBIAN/postrm"

chmod 755 "${BUILD_DIR}/DEBIAN/postinst"
chmod 755 "${BUILD_DIR}/DEBIAN/postrm"
chmod 644 "${BUILD_DIR}/DEBIAN/control"

# Compute installed size in KB
INSTALLED_SIZE=$(du -sk "${BUILD_DIR}/usr" | awk '{print $1}')
echo "Installed-Size: ${INSTALLED_SIZE}" >> "${BUILD_DIR}/DEBIAN/control"

# 7. Build .deb package using dpkg-deb
TARGET_DEB="${DIST_DIR}/${DEB_NAME}"
echo "Running dpkg-deb to package ${TARGET_DEB}..."
dpkg-deb --build --root-owner-group "${BUILD_DIR}" "${TARGET_DEB}"

# 8. Compute SHA-256 Checksum
SHA256=$(sha256sum "${TARGET_DEB}" | awk '{print $1}')
echo "${SHA256}  ${DEB_NAME}" > "${DIST_DIR}/${DEB_NAME}.sha256"

echo "=== Package Build Successful! ==="
echo "Package File: ${TARGET_DEB}"
echo "SHA-256:      ${SHA256}"
echo ""
echo "=== Package Metadata ==="
dpkg-deb -I "${TARGET_DEB}"
echo ""
echo "=== Package Contents ==="
dpkg-deb -c "${TARGET_DEB}"
