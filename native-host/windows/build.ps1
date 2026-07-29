$ErrorActionPreference = "Stop"
$ProjectDirectory = $PSScriptRoot
$OutputDirectory = Join-Path $ProjectDirectory "dist/windows"
$BuildDirectory = Join-Path $ProjectDirectory "bin/Release/net462"

if (Test-Path -LiteralPath $OutputDirectory) {
    Remove-Item -Recurse -Force -LiteralPath $OutputDirectory
}
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null

dotnet build (Join-Path $ProjectDirectory "ChromeVerticalTabsToggle.csproj") `
    --configuration Release

Copy-Item (Join-Path $BuildDirectory "ChromeVerticalTabsToggle.exe") $OutputDirectory
Copy-Item (Join-Path $BuildDirectory "ChromeVerticalTabsToggle.exe.config") $OutputDirectory
Copy-Item (Join-Path $ProjectDirectory "../resources/sidebar-labels.json") $OutputDirectory
Copy-Item (Join-Path $ProjectDirectory "../../extension/native-host-contract.json") $OutputDirectory
Copy-Item (Join-Path $ProjectDirectory "install.ps1") $OutputDirectory
Copy-Item (Join-Path $ProjectDirectory "install.cmd") $OutputDirectory
