$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Net.Http

$baseUrl = [Uri]"https://tuyendung.vnptmoney.vn/"
$rootDir = (Get-Location).Path

$handler = [System.Net.Http.HttpClientHandler]::new()
$handler.AutomaticDecompression = [System.Net.DecompressionMethods]::GZip -bor [System.Net.DecompressionMethods]::Deflate
$client = [System.Net.Http.HttpClient]::new($handler)
$client.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0")

$htmlQueue = [System.Collections.Generic.Queue[Uri]]::new()
$htmlQueue.Enqueue($baseUrl)

$visitedHtml = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$downloadedAssets = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$parsedTextAssets = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

function Resolve-TargetPath {
    param(
        [Uri]$Uri
    )

    $relativePath = $Uri.AbsolutePath.TrimStart("/")
    if ([string]::IsNullOrWhiteSpace($relativePath)) {
        return Join-Path $rootDir "index.html"
    }

    if ($relativePath.EndsWith("/")) {
        $relativePath = $relativePath.TrimEnd("/") + "/index.html"
    }

    $segments = $relativePath -split "/"
    $current = $rootDir

    for ($i = 0; $i -lt $segments.Length; $i++) {
        $segment = $segments[$i]
        if ([string]::IsNullOrWhiteSpace($segment)) {
            continue
        }

        if ($i -eq $segments.Length - 1) {
            return Join-Path $current $segment
        }

        $current = Join-Path $current $segment
    }

    return Join-Path $rootDir $relativePath
}

function Ensure-ParentDirectory {
    param(
        [string]$FilePath
    )

    $parent = Split-Path -Parent $FilePath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
}

function Normalize-Url {
    param(
        [string]$Value,
        [Uri]$CurrentUri
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }

    $clean = $Value.Trim()
    $clean = $clean.Trim("'`"")

    if ($clean.StartsWith("data:", [System.StringComparison]::OrdinalIgnoreCase)) {
        return $null
    }

    if ($clean.StartsWith("javascript:", [System.StringComparison]::OrdinalIgnoreCase)) {
        return $null
    }

    if ($clean.StartsWith("#")) {
        return $null
    }

    try {
        if ([Uri]::IsWellFormedUriString($clean, [UriKind]::Absolute)) {
            return [Uri]$clean
        }

        return [Uri]::new($CurrentUri, $clean)
    }
    catch {
        return $null
    }
}

function Save-Content {
    param(
        [Uri]$Uri,
        [byte[]]$Bytes
    )

    $targetPath = Resolve-TargetPath -Uri $Uri
    Ensure-ParentDirectory -FilePath $targetPath
    [System.IO.File]::WriteAllBytes($targetPath, $Bytes)
}

function Download-Uri {
    param(
        [Uri]$Uri
    )

    $response = $client.GetAsync($Uri.AbsoluteUri).GetAwaiter().GetResult()
    $response.EnsureSuccessStatusCode() | Out-Null
    $bytes = $response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
    Save-Content -Uri $Uri -Bytes $bytes

    return @{
        ContentType = $response.Content.Headers.ContentType.MediaType
        Text = [System.Text.Encoding]::UTF8.GetString($bytes)
    }
}

function Queue-Html {
    param(
        [Uri]$Uri
    )

    if ($Uri.Host -ne $baseUrl.Host) {
        return
    }

    $path = $Uri.AbsolutePath.ToLowerInvariant()
    if ($path -eq "/" -or $path.EndsWith(".html")) {
        if ($visitedHtml.Add($Uri.AbsoluteUri)) {
            $htmlQueue.Enqueue($Uri)
        }
    }
}

function Download-Asset {
    param(
        [Uri]$Uri
    )

    if ($Uri.Host -ne $baseUrl.Host) {
        return
    }

    if (-not $downloadedAssets.Add($Uri.AbsoluteUri)) {
        return
    }

    $result = Download-Uri -Uri $Uri
    $path = $Uri.AbsolutePath.ToLowerInvariant()
    if (($path.EndsWith(".css") -or $path.EndsWith(".svg")) -and $parsedTextAssets.Add($Uri.AbsoluteUri)) {
        Extract-Links -Text $result.Text -CurrentUri $Uri
    }
}

function Extract-Links {
    param(
        [string]$Text,
        [Uri]$CurrentUri
    )

    $patterns = @(
        'href\s*=\s*["''](?<url>[^"'']+)["'']',
        'src\s*=\s*["''](?<url>[^"'']+)["'']',
        'url\((?<quote>["'']?)(?<url>[^)"'']+)\k<quote>\)'
    )

    foreach ($pattern in $patterns) {
        foreach ($match in [regex]::Matches($Text, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
            $normalized = Normalize-Url -Value $match.Groups["url"].Value -CurrentUri $CurrentUri
            if ($null -eq $normalized) {
                continue
            }

            if ($normalized.Host -ne $baseUrl.Host) {
                continue
            }

            $absolute = $normalized.AbsolutePath.ToLowerInvariant()
            if ($absolute -eq "/" -or $absolute.EndsWith(".html")) {
                Queue-Html -Uri $normalized
                continue
            }

            Download-Asset -Uri $normalized
        }
    }
}

while ($htmlQueue.Count -gt 0) {
    $current = $htmlQueue.Dequeue()
    Write-Host "Mirroring $($current.AbsoluteUri)"
    $result = Download-Uri -Uri $current
    Extract-Links -Text $result.Text -CurrentUri $current
}

$client.Dispose()
$handler.Dispose()

Write-Host "Mirror completed in $rootDir"
