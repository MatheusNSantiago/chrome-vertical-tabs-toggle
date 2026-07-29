param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[a-p]{32}$")]
    [string]$ExtensionId
)

$ErrorActionPreference = "Stop"
$BundleDirectory = $PSScriptRoot
$ContractPath = Join-Path $BundleDirectory "native-host-contract.json"
$Contract = Get-Content -Raw -LiteralPath $ContractPath | ConvertFrom-Json
if ($Contract.schema_version -ne 1) {
    throw "Unsupported native host contract"
}

$InstallDirectory = Join-Path $env:LOCALAPPDATA "Chrome Vertical Tabs Toggle"
$ManifestPath = Join-Path $InstallDirectory "$($Contract.name).json"
$HostPath = Join-Path $InstallDirectory "ChromeVerticalTabsToggle.exe"
$RegistryPaths = @(
    "HKCU:\Software\Google\Chrome\NativeMessagingHosts\$($Contract.name)",
    "HKCU:\Software\Chromium\NativeMessagingHosts\$($Contract.name)"
)

New-Item -ItemType Directory -Force -Path $InstallDirectory | Out-Null
Copy-Item (Join-Path $BundleDirectory "ChromeVerticalTabsToggle.exe") $HostPath
Copy-Item (Join-Path $BundleDirectory "ChromeVerticalTabsToggle.exe.config") $InstallDirectory
Copy-Item (Join-Path $BundleDirectory "sidebar-labels.json") $InstallDirectory

$AllowedOrigins = @("chrome-extension://$ExtensionId/")
if (Test-Path -LiteralPath $ManifestPath) {
    $InstalledManifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json
    $AllowedOrigins += $InstalledManifest.allowed_origins
}
$Manifest = @{
    name = $Contract.name
    description = $Contract.description
    path = $HostPath
    type = "stdio"
    allowed_origins = @($AllowedOrigins | Sort-Object -Unique)
}
$ManifestJson = $Manifest | ConvertTo-Json
[IO.File]::WriteAllText($ManifestPath, $ManifestJson, [Text.UTF8Encoding]::new($false))

foreach ($RegistryPath in $RegistryPaths) {
    New-Item -Force -Path $RegistryPath | Out-Null
    Set-Item -Path $RegistryPath -Value $ManifestPath
}

Write-Host "Installed. Restart Chrome once."
