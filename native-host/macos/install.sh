#!/bin/sh
set -eu

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
contract_path="$script_directory/native-host-contract.json"
contract_schema=$(/usr/bin/plutil -extract schema_version raw -o - "$contract_path")
host_name=$(/usr/bin/plutil -extract name raw -o - "$contract_path")
host_description=$(/usr/bin/plutil -extract description raw -o - "$contract_path")
extension_id=$(/usr/bin/plutil -extract extension_id raw -o - "$contract_path")
install_directory="$HOME/Library/Application Support/Chrome Vertical Tabs Toggle"
application_name="Chrome Vertical Tabs Toggle.app"
application_path="$install_directory/$application_name"
host_path="$application_path/Contents/MacOS/ChromeVerticalTabsToggle"
allowed_origin="chrome-extension://$extension_id/"

if [ "$contract_schema" != "2" ]; then
  printf '%s\n' "Unsupported native host contract" >&2
  exit 1
fi

mkdir -p "$install_directory"
rm -rf "$application_path"
cp -R "$script_directory/$application_name" "$application_path"

for product_directory in \
  "Google/Chrome" \
  "Google/Chrome Beta" \
  "Google/Chrome Dev" \
  "Google/Chrome Canary" \
  "Google/ChromeForTesting" \
  "Chromium"
do
  manifest_directory="$HOME/Library/Application Support/$product_directory/NativeMessagingHosts"
  manifest_path="$manifest_directory/$host_name.json"
  manifest_working_copy=$(mktemp "${TMPDIR:-/tmp}/chrome-vertical-tabs-toggle.XXXXXX")
  mkdir -p "$manifest_directory"

  cat > "$manifest_working_copy" <<EOF
{
  "name": "",
  "description": "",
  "path": "",
  "type": "stdio",
  "allowed_origins": []
}
EOF

  /usr/bin/plutil -replace name -string "$host_name" "$manifest_working_copy"
  /usr/bin/plutil -replace description -string "$host_description" "$manifest_working_copy"
  /usr/bin/plutil -replace path -string "$host_path" "$manifest_working_copy"
  /usr/bin/plutil -replace type -string "stdio" "$manifest_working_copy"
  /usr/bin/plutil -insert allowed_origins.0 -string "$allowed_origin" "$manifest_working_copy"
  /usr/bin/plutil -convert json -o "$manifest_path" "$manifest_working_copy"
  rm "$manifest_working_copy"
done

open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
printf '%s\n' "Installed. Add '$application_name' to Accessibility, then restart Chrome once."
