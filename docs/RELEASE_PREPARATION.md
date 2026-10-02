# v0.2.0 publication handoff

V2 is prepared locally. No remote push, GitHub release creation, asset upload or public deployment was performed during this preparation. The existing workflow validates content and Python tests with read-only repository permission; it does not publish releases. The v0.1 publication authorization recorded in the historical build status applied to that release.

The local `v0.2.0` tag identifies the prepared source commit. The four upload assets are in `dist/release/`: `domes-for-dots-v0.2.0-source.zip`, `domes-for-dots-v0.2.0-web.zip`, `SHA256SUMS` and `release_manifest.json`. The [V2 build record](V2_BUILD.md) records local acceptance. The [prepared release body](releases/v0.2.0.md) is ready to paste into GitHub.

The build manifest can identify an earlier clean runtime commit than the release tag: later documentation/evidence commits do not change the verified runtime hashes. The package receipt must identify the tagged release commit. Final ZIP checksums stay outside the source archive to avoid a self-referential checksum.

## 1. Check the prepared local files

Run these commands from the repository root in PowerShell. Stop if any check fails; do not overwrite the tag or force-push to resolve a mismatch.

```powershell
if (git status --porcelain) { throw 'Working tree is not clean.' }
$releaseCommit = git rev-parse 'v0.2.0^{}'
if ($LASTEXITCODE -ne 0) { throw 'Local v0.2.0 tag is missing.' }
$releaseReceipt = Get-Content -LiteralPath 'dist/release/release_manifest.json' -Raw | ConvertFrom-Json
if ($releaseReceipt.version -ne '0.2.0' -or $releaseReceipt.candidate -ne $false -or $releaseReceipt.source_commit -ne $releaseCommit) {
    throw 'Release receipt does not identify the prepared tag.'
}
$releaseAssetNames = @('domes-for-dots-v0.2.0-source.zip', 'domes-for-dots-v0.2.0-web.zip', 'SHA256SUMS', 'release_manifest.json')
foreach ($assetName in $releaseAssetNames) {
    if (-not (Test-Path -LiteralPath "dist/release/$assetName" -PathType Leaf)) { throw "Missing asset: $assetName" }
}
foreach ($checksumLine in Get-Content -LiteralPath 'dist/release/SHA256SUMS') {
    $checksumParts = $checksumLine -split '\s+', 2
    $actualHash = (Get-FileHash -LiteralPath "dist/release/$($checksumParts[1])" -Algorithm SHA256).Hash
    if ($actualHash -ne $checksumParts[0]) { throw "Checksum mismatch: $($checksumParts[1])" }
}
git show --no-patch --format=fuller v0.2.0
```

## 2. Push the reviewed commit and tag

This is the first public write. When ready to publish the prepared V2 source, push the local `main` history and the existing tag:

```powershell
git push origin main refs/tags/v0.2.0
```

If Git reports a rejected push, inspect the remote changes and reconcile them before continuing. Do not force-push or recreate the tag. Any runtime source change requires a new build and acceptance; changed packaged source requires a new package receipt and checksums before release.

## 3. Wait for GitHub validation

Open [Validate content and contracts](https://github.com/bslizzle8552/domes-for-dots/actions/workflows/validate.yml). Select the push run for the commit printed by `git rev-parse 'v0.2.0^{}'` and require a successful result. The workflow checks schemas/content and Python tests; the native Godot, exported-browser and archive acceptance remain the local evidence in `docs/V2_BUILD.md`.

## 4. Publish the GitHub release

Open the repository's [Releases page](https://github.com/bslizzle8552/domes-for-dots/releases) and create a new release:

1. Select the existing **`v0.2.0`** tag. Do not create a new tag from another branch tip.
2. Set the title to **Domes for Dots v0.2.0**.
3. Paste the contents of [`docs/releases/v0.2.0.md`](releases/v0.2.0.md) into the release description.
4. Attach the four files from `dist/release/` listed above. GitHub's automatically generated source archives are separate from the verified source ZIP.
5. Publish the release after reviewing the tag, description and four attachments.

The expected release address is [v0.2.0](https://github.com/bslizzle8552/domes-for-dots/releases/tag/v0.2.0). It will not exist publicly until this step succeeds. A GitHub release does not deploy the Web world to a public host.

## 5. Verify the public downloads

After publication, use an unauthenticated download and compare every uploaded asset with the prepared local copy. The following PowerShell commands send no authorization headers and save downloads in a new ignored evidence folder:

```powershell
$publicDownloadDirectory = Join-Path (Get-Location) ('artifacts/release-public-v0.2.0-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $publicDownloadDirectory | Out-Null
$releaseAssetNames = @('domes-for-dots-v0.2.0-source.zip', 'domes-for-dots-v0.2.0-web.zip', 'SHA256SUMS', 'release_manifest.json')
foreach ($assetName in $releaseAssetNames) {
    $downloadPath = Join-Path $publicDownloadDirectory $assetName
    Invoke-WebRequest -Uri "https://github.com/bslizzle8552/domes-for-dots/releases/download/v0.2.0/$assetName" -OutFile $downloadPath
    $downloadHash = (Get-FileHash -LiteralPath $downloadPath -Algorithm SHA256).Hash
    $preparedHash = (Get-FileHash -LiteralPath "dist/release/$assetName" -Algorithm SHA256).Hash
    if ($downloadHash -ne $preparedHash) { throw "Public download mismatch: $assetName" }
    Write-Output "PASS: $assetName $downloadHash"
}
```

Record the release URL, successful CI run URL and download verification result in a subsequent documentation-only commit on `main`. Keep the published tag fixed. Publication and public-download verification are pending until the owner completes these steps; no additional product changes are required for this handoff.
