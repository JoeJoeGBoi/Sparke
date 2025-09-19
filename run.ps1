<#
.SYNOPSIS
    Build and run the Discord invite-role bot inside Docker.

.DESCRIPTION
    This script builds the Docker image defined by the local Dockerfile and
    starts a container with the DISCORD_TOKEN environment variable passed
    through. Provide the token either as a parameter or via the environment.

.PARAMETER Token
    Optional bot token. If omitted the script reads the value from the
    DISCORD_TOKEN environment variable in the current PowerShell session.

.PARAMETER BuildOnly
    When specified, the script only builds the Docker image without running
    the container.

.EXAMPLE
    PS> $env:DISCORD_TOKEN = "<your token>"
    PS> ./run.ps1

.EXAMPLE
    PS> ./run.ps1 -Token "<your token>" -BuildOnly

#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$Token,

    [Parameter(Mandatory = $false)]
    [switch]$BuildOnly
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$imageName = "sparke-discord-bot"

if (-not $Token) {
    $Token = $Env:DISCORD_TOKEN
}

if (-not $Token -and -not $BuildOnly.IsPresent) {
    throw "Discord bot token not provided. Set DISCORD_TOKEN or pass -Token."
}

Write-Host "📦 Building Docker image '$imageName'..." -ForegroundColor Cyan
docker build --pull --tag $imageName .

if ($BuildOnly.IsPresent) {
    Write-Host "Docker image built successfully." -ForegroundColor Green
    return
}

Write-Host "🚀 Starting Discord bot container..." -ForegroundColor Cyan
$dockerArgs = @(
    "run",
    "--rm",
    "--name", $imageName,
    "--env", "DISCORD_TOKEN=$Token",
    $imageName
)

docker @dockerArgs
