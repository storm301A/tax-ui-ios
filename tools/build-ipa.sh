#!/usr/bin/env bash
# 在 macOS 上本地出未签名 ipa（Windows 上跑不了，用 GitHub Actions 代替）
# 用法：bash tools/build-ipa.sh

set -euo pipefail
cd "$(dirname "$0")/.."

npx cap sync ios

OUT="$PWD/build"
rm -rf "$OUT"
mkdir -p "$OUT"

cd ios/App
xcodebuild \
  -workspace App.xcworkspace \
  -scheme App \
  -configuration Release \
  -sdk iphoneos \
  -destination 'generic/platform=iOS' \
  -archivePath "$OUT/App.xcarchive" \
  CODE_SIGNING_ALLOWED=NO \
  CODE_SIGNING_REQUIRED=NO \
  CODE_SIGN_IDENTITY="" \
  archive

APP="$OUT/App.xcarchive/Products/Applications/App.app"
mkdir -p "$OUT/Payload"
cp -R "$APP" "$OUT/Payload/"
cd "$OUT"
zip -qry taxui-unsigned.ipa Payload

echo
echo "OK: $OUT/taxui-unsigned.ipa"
