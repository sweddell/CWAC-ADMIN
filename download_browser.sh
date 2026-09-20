#!/bin/bash
# Download Chrome for Testing and ChromeDriver
# Version: 122.0.6261.39

set -e

CHROME_VERSION="122.0.6261.39"
PLATFORM="mac-arm64"

echo "📥 Downloading Chrome for Testing and ChromeDriver..."
echo "Version: $CHROME_VERSION"
echo "Platform: $PLATFORM"
echo ""

# Create directories
mkdir -p chrome
mkdir -p drivers

cd chrome

# Download Chrome for Testing
echo "Downloading Chrome for Testing..."
CHROME_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/${PLATFORM}/chrome-${PLATFORM}.zip"
curl -L -o chrome.zip "$CHROME_URL"

# Extract Chrome
echo "Extracting Chrome..."
unzip -q chrome.zip
# Keep the chrome-mac-arm64 folder structure that CWAC expects
mkdir -p mac_arm-${CHROME_VERSION}
mv chrome-${PLATFORM} mac_arm-${CHROME_VERSION}/
rm chrome.zip

echo "✅ Chrome installed to: chrome/mac_arm-${CHROME_VERSION}/chrome-${PLATFORM}/"

cd ..
cd drivers

# Download ChromeDriver
echo ""
echo "Downloading ChromeDriver..."
DRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/${PLATFORM}/chromedriver-${PLATFORM}.zip"
curl -L -o chromedriver.zip "$DRIVER_URL"

# Extract ChromeDriver
echo "Extracting ChromeDriver..."
unzip -q chromedriver.zip
mv chromedriver-${PLATFORM}/chromedriver chromedriver_mac_arm64
chmod +x chromedriver_mac_arm64
rm -rf chromedriver-${PLATFORM}
rm chromedriver.zip

echo "✅ ChromeDriver installed to: drivers/chromedriver_mac_arm64"

cd ..

# Remove macOS quarantine attributes and sign binaries
echo ""
echo "Removing macOS security restrictions..."
chmod -R 755 chrome/mac_arm-${CHROME_VERSION}/
chmod +x drivers/chromedriver_mac_arm64

# Remove quarantine
xattr -cr chrome/mac_arm-${CHROME_VERSION}/ 2>/dev/null || true

# Ad-hoc sign binaries to prevent macOS Gatekeeper blocking
echo "Signing Chrome and ChromeDriver..."
codesign --force --deep --sign - "chrome/mac_arm-${CHROME_VERSION}/chrome-${PLATFORM}/Google Chrome for Testing.app" 2>/dev/null || \
  echo "⚠️  Note: If scans fail, run: codesign --force --deep --sign - chrome/mac_arm-.../chrome-mac-arm64/Google\ Chrome\ for\ Testing.app"
codesign --force --deep --sign - drivers/chromedriver_mac_arm64 2>/dev/null || true

echo ""
echo "🎉 Browser setup complete!"
echo ""
echo "Chrome: ./chrome/mac_arm-${CHROME_VERSION}/"
echo "Driver: ./drivers/chromedriver_mac_arm64"
echo ""
echo "✅ Security attributes cleared"
echo ""
echo "📦 Installing JavaScript dependencies (axe-core, readability)..."
npm install
echo ""
echo "✅ All dependencies installed!"
