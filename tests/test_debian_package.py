"""
Unit tests validating Debian package metadata, dependencies, and desktop entry specifications.
"""

from pathlib import Path
import unittest

from droidbridge.constants import APP_ID, APP_VERSION


class TestDebianPackage(unittest.TestCase):

    def setUp(self):
        self.root = Path(__file__).parent.parent
        self.control_path = self.root / "packaging" / "debian" / "control"
        self.desktop_path = self.root / "data" / "org.droidbridge.DroidBridge.desktop"
        self.icon_path = self.root / "data" / "icons" / "scalable" / "apps" / "org.droidbridge.DroidBridge.svg"
        self.changelog_path = self.root / "packaging" / "debian" / "changelog"

    def test_debian_control_metadata(self):
        self.assertTrue(self.control_path.exists(), "packaging/debian/control must exist")
        content = self.control_path.read_text(encoding="utf-8")

        self.assertIn("Package: droidbridge", content)
        self.assertIn("Architecture: all", content)
        self.assertIn("gir1.2-gtk-4.0", content)
        self.assertIn("python3-gi", content)
        self.assertIn("scrcpy (>= 2.0)", content)
        self.assertIn("adb | android-tools-adb", content)
        self.assertIn("gir1.2-adw-1", content)

    def test_desktop_file_specification(self):
        self.assertTrue(self.desktop_path.exists(), "Desktop file must exist")
        content = self.desktop_path.read_text(encoding="utf-8")

        self.assertIn("[Desktop Entry]", content)
        self.assertIn("Type=Application", content)
        self.assertIn("Name=DroidBridge", content)
        self.assertIn("Exec=droidbridge", content)
        self.assertIn(f"Icon={APP_ID}", content)
        self.assertIn(f"StartupWMClass={APP_ID}", content)
        self.assertIn("Categories=", content)

    def test_scalable_icon_exists(self):
        self.assertTrue(self.icon_path.exists(), "Scalable SVG icon must exist")
        svg_content = self.icon_path.read_text(encoding="utf-8")
        self.assertIn("<svg", svg_content)
        self.assertIn("</svg>", svg_content)

    def test_changelog_version(self):
        self.assertTrue(self.changelog_path.exists(), "Changelog must exist")
        content = self.changelog_path.read_text(encoding="utf-8")
        self.assertIn(f"droidbridge ({APP_VERSION}-1)", content)


if __name__ == "__main__":
    unittest.main()
