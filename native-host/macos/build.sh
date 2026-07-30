#!/bin/sh
set -eu

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
output_directory="$script_directory/dist"
application_path="$output_directory/Chrome Vertical Tabs Toggle.app"
executable_directory="$application_path/Contents/MacOS"
executable_path="$executable_directory/ChromeVerticalTabsToggle"

rm -rf "$output_directory"
mkdir -p "$executable_directory" "$application_path/Contents/Resources"

for architecture in arm64 x86_64
do
  swiftc "$script_directory/main.swift" \
    -target "$architecture-apple-macosx13.0" \
    -framework AppKit \
    -framework ApplicationServices \
    -o "$executable_directory/ChromeVerticalTabsToggle-$architecture"
done
lipo -create \
  "$executable_directory/ChromeVerticalTabsToggle-arm64" \
  "$executable_directory/ChromeVerticalTabsToggle-x86_64" \
  -output "$executable_path"
rm "$executable_directory/ChromeVerticalTabsToggle-arm64"
rm "$executable_directory/ChromeVerticalTabsToggle-x86_64"

cp "$script_directory/Info.plist" "$application_path/Contents/Info.plist"
cp "$script_directory/../resources/sidebar-labels.json" "$application_path/Contents/Resources/sidebar-labels.json"
cp "$script_directory/install.sh" "$output_directory/install.sh"
cp "$script_directory/../../extension/native-host-contract.json" "$output_directory/native-host-contract.json"
codesign --force --sign - --identifier dev.matheus.chrome-vertical-tabs-toggle "$application_path"
