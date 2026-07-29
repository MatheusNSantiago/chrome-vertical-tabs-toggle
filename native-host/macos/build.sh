#!/bin/sh
set -eu

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
output_directory="$script_directory/dist"
application_path="$output_directory/Chrome Vertical Tabs Toggle.app"

rm -rf "$output_directory"
mkdir -p "$application_path/Contents/MacOS" "$application_path/Contents/Resources"

swiftc "$script_directory/main.swift" \
  -framework AppKit \
  -framework ApplicationServices \
  -o "$application_path/Contents/MacOS/ChromeVerticalTabsToggle"
cp "$script_directory/Info.plist" "$application_path/Contents/Info.plist"
cp "$script_directory/../resources/sidebar-labels.json" "$application_path/Contents/Resources/sidebar-labels.json"
cp "$script_directory/install.sh" "$output_directory/install.sh"
cp "$script_directory/../../extension/native-host-contract.json" "$output_directory/native-host-contract.json"
codesign --force --sign - --identifier dev.matheus.chrome-vertical-tabs-toggle "$application_path"
