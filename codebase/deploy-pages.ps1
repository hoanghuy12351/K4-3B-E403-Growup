param(
    [ValidateSet('Inspect', 'Publish', 'Status')]
    [string]$Mode = 'Inspect'
)

$ErrorActionPreference = 'Stop'
$repoOwner = 'hoanghuy12351'
$repoName = 'K4-3B-E403-Growup'
$apiBase = "https://api.github.com/repos/$repoOwner/$repoName"
$deployBranch = 'codex/cp2-pages'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$stageDirectory = Join-Path $projectDirectory '.cp2-publish'
$siteFiles = @('index.html', 'styles.css', 'app.js')

# The existing Git credential manager is the authentication source.
# Capture its output in memory. Never print or persist credentials.
$env:GIT_TERMINAL_PROMPT = '0'
$env:GCM_INTERACTIVE = 'Never'
$credentialInput = "protocol=https`nhost=github.com`npath=$repoOwner/$repoName.git`n`n"
$credentialOutput = $credentialInput | git credential fill 2>$null
if ($LASTEXITCODE -ne 0) {
    throw 'No usable GitHub credential. Sign in to GitHub with Git Credential Manager and retry.'
}
$credentialMap = @{}
foreach ($line in $credentialOutput) {
    if ($line -match '^([^=]+)=(.*)$') { $credentialMap[$Matches[1]] = $Matches[2] }
}
if (-not $credentialMap['password']) { throw 'GitHub credential did not include an access token.' }
$requestHeaders = @{
    Authorization = 'Bearer ' + $credentialMap['password']
    Accept = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2026-03-10'
    'User-Agent' = 'Growup-CP2-Deployment'
}
$credentialOutput = $null
$credentialMap = $null

function Invoke-GitHubRequest {
    param([string]$Method, [string]$Url, [object]$Body = $null)
    $parameters = @{ Method = $Method; Uri = $Url; Headers = $requestHeaders; TimeoutSec = 30 }
    if ($null -ne $Body) {
        $parameters.ContentType = 'application/json'
        $parameters.Body = ConvertTo-Json -InputObject $Body -Depth 10 -Compress
    }
    try { return Invoke-RestMethod @parameters }
    catch {
        $responseCode = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        if ($Method -eq 'GET' -and $responseCode -eq 404) { return $null }
        # Do not dump request objects or headers on errors.
        throw "GitHub request failed: $Method $Url (HTTP $responseCode)."
    }
}

$repository = Invoke-GitHubRequest -Method GET -Url $apiBase
if (-not $repository) { throw 'Repository is not accessible to the current GitHub account.' }
$pages = Invoke-GitHubRequest -Method GET -Url "$apiBase/pages"

if ($Mode -eq 'Inspect') {
    [pscustomobject]@{
        repository = $repository.full_name
        private = $repository.private
        can_administer = $repository.permissions.admin
        can_push = $repository.permissions.push
        pages_exists = [bool]$pages
        pages_url = $pages.html_url
        pages_branch = $pages.source.branch
        pages_path = $pages.source.path
    } | ConvertTo-Json
    exit 0
}

if ($Mode -eq 'Status') {
    if (-not $pages) { throw 'GitHub Pages has not been enabled.' }
    $build = Invoke-GitHubRequest -Method GET -Url "$apiBase/pages/builds/latest"
    $expectedDeploymentFile = Join-Path $PSScriptRoot 'deployment.json'
    $expectedCommit = if (Test-Path -LiteralPath $expectedDeploymentFile) { (Get-Content -Raw -LiteralPath $expectedDeploymentFile | ConvertFrom-Json).commit } else { $null }
    [pscustomobject]@{
        url = $pages.html_url
        site_status = $pages.status
        build_status = $build.status
        commit = $build.commit
        matches_expected_commit = ($null -ne $expectedCommit -and $build.commit -eq $expectedCommit)
        error = $build.error.message
    } | ConvertTo-Json
    exit 0
}

if (-not $repository.permissions.push) { throw 'Current GitHub account cannot push to this repository.' }
if ($pages -and ($pages.source.branch -ne $deployBranch -or $pages.source.path -ne '/')) {
    throw 'An existing Pages site uses another source. Its settings were left unchanged.'
}

$remoteUrl = "https://github.com/$repoOwner/$repoName.git"
$remoteBranch = Invoke-GitHubRequest -Method GET -Url "$apiBase/git/ref/heads/$deployBranch"
if ($remoteBranch) {
    if (-not (Test-Path -LiteralPath (Join-Path $stageDirectory '.git'))) { throw 'Existing deployment branch has no matching local checkout. Inspect it before updating.' }
    $stageBranch = git -C $stageDirectory branch --show-current
    $stageRemote = git -C $stageDirectory remote get-url origin
    $stageChanges = git -C $stageDirectory status --porcelain
    if ($stageBranch -ne $deployBranch -or $stageRemote -ne $remoteUrl -or $stageChanges) { throw 'Deployment checkout has unexpected settings or local changes. Inspect before updating.' }
    git -C $stageDirectory fetch origin $deployBranch
    if ($LASTEXITCODE -ne 0) { throw 'Could not fetch the current deployment branch.' }
    git -C $stageDirectory merge --ff-only FETCH_HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Deployment source diverged. No forced update was attempted.' }
    $allowedFiles = @('.nojekyll', 'README.md', 'app.js', 'index.html', 'styles.css')
    $unexpectedFiles = @(git -C $stageDirectory ls-files | Where-Object { $_ -notin $allowedFiles })
    if ($unexpectedFiles.Count) { throw 'Deployment branch includes unexpected files. Inspect before publishing.' }
} else {
    if (Test-Path -LiteralPath $stageDirectory) { throw 'Deployment staging directory already exists. Inspect it before reusing.' }
    New-Item -ItemType Directory -Path $stageDirectory | Out-Null
    git -C $stageDirectory init -b $deployBranch
    if ($LASTEXITCODE -ne 0) { throw 'Could not initialize deployment source.' }
    git -C $stageDirectory remote add origin $remoteUrl
    if ($LASTEXITCODE -ne 0) { throw 'Could not configure deployment source.' }
}

# An isolated source tree prevents the course data and its history being deployed.
foreach ($file in $siteFiles) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination (Join-Path $stageDirectory $file)
}
[System.IO.File]::WriteAllText((Join-Path $stageDirectory '.nojekyll'), '')
[System.IO.File]::WriteAllText((Join-Path $stageDirectory 'README.md'), "# Growup CP2`n`nStatic mock prototype with synthetic data. No AI call or live VLearn connection.`n", [System.Text.UTF8Encoding]::new($false))

$gitAuthorName = git config user.name
$gitAuthorEmail = git config user.email
if (-not $gitAuthorName -or -not $gitAuthorEmail) { throw 'Git author identity is missing.' }
git -C $stageDirectory config user.name $gitAuthorName
git -C $stageDirectory config user.email $gitAuthorEmail
git -C $stageDirectory add -- index.html styles.css app.js .nojekyll README.md
if ($LASTEXITCODE -ne 0) { throw 'Could not stage deployment source.' }
git -C $stageDirectory diff --cached --quiet
if ($LASTEXITCODE -eq 1) {
    git -C $stageDirectory commit -m 'Update CP2 scope selection and teacher question approval'
    if ($LASTEXITCODE -ne 0) { throw 'Could not commit deployment source.' }
} elseif ($LASTEXITCODE -ne 0) { throw 'Could not inspect staged deployment source.' }
git -C $stageDirectory push origin "HEAD:refs/heads/$deployBranch"
if ($LASTEXITCODE -ne 0) { throw 'Could not push deployment branch.' }
$sourceCommit = git -C $stageDirectory rev-parse --verify HEAD

if (-not $pages) {
    $pages = Invoke-GitHubRequest -Method POST -Url "$apiBase/pages" -Body @{
        build_type = 'legacy'
        source = @{ branch = $deployBranch; path = '/' }
    }
}

[pscustomobject]@{
    provider = 'GitHub Pages'
    url = $pages.html_url
    branch = $deployBranch
    commit = $sourceCommit
    status = 'pending'
    repository = $remoteUrl
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'deployment.json') -Encoding utf8
Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'deployment.json')
