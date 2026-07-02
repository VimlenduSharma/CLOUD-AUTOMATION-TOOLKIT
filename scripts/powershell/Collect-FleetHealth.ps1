param(
    [Parameter(Mandatory = $true)]
    [string]$ApiUrl,

    [string]$Endpoint = "https://github.com",
    [string[]]$RequiredServices = @("WinRM", "EventLog", "LanmanServer"),
    [int]$CpuWarnPercent = 75,
    [int]$MemoryWarnPercent = 75
)

$ErrorActionPreference = "Stop"

function Get-CpuPercent {
    $sample = Get-CimInstance -ClassName Win32_Processor
    return [math]::Round(($sample | Measure-Object -Property LoadPercentage -Average).Average, 2)
}

function Get-MemoryPercent {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    $used = $os.TotalVisibleMemorySize - $os.FreePhysicalMemory
    return [math]::Round(($used / $os.TotalVisibleMemorySize) * 100, 2)
}

function Test-HttpEndpoint {
    param([string]$Url)
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        $timer.Stop()
        return @{
            name = "http_endpoint"
            status = if ($response.StatusCode -lt 400) { "pass" } else { "warn" }
            message = "$Url returned HTTP $($response.StatusCode)."
            latency_ms = $timer.ElapsedMilliseconds
            metadata = @{ url = $Url; status_code = $response.StatusCode }
        }
    }
    catch {
        $timer.Stop()
        return @{
            name = "http_endpoint"
            status = "fail"
            message = "$Url failed: $($_.Exception.Message)"
            latency_ms = $timer.ElapsedMilliseconds
            metadata = @{ url = $Url }
        }
    }
}

function Test-DnsResolution {
    param([string]$Hostname)
    try {
        $records = Resolve-DnsName -Name $Hostname -ErrorAction Stop
        return @{
            name = "dns_resolution"
            status = "pass"
            message = "$Hostname resolved."
            metadata = @{ hostname = $Hostname; addresses = @($records.IPAddress | Where-Object { $_ }) }
        }
    }
    catch {
        return @{
            name = "dns_resolution"
            status = "fail"
            message = "$Hostname failed DNS lookup: $($_.Exception.Message)"
            metadata = @{ hostname = $Hostname }
        }
    }
}

function Test-TcpConnectivity {
    param([string]$Hostname, [int]$Port)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $connect = $client.BeginConnect($Hostname, $Port, $null, $null)
        $connected = $connect.AsyncWaitHandle.WaitOne(3000, $false)
        if ($connected) {
            $client.EndConnect($connect)
        }
        return @{
            name = "tcp_connectivity"
            status = if ($connected) { "pass" } else { "fail" }
            message = if ($connected) { "Connected to $Hostname`:$Port." } else { "Timeout connecting to $Hostname`:$Port." }
            metadata = @{ hostname = $Hostname; port = $Port }
        }
    }
    catch {
        return @{
            name = "tcp_connectivity"
            status = "fail"
            message = "Could not connect to $Hostname`:$Port: $($_.Exception.Message)"
            metadata = @{ hostname = $Hostname; port = $Port }
        }
    }
    finally {
        $client.Close()
    }
}

$cpu = Get-CpuPercent
$memory = Get-MemoryPercent
$serviceStates = foreach ($service in $RequiredServices) {
    $item = Get-Service -Name $service -ErrorAction SilentlyContinue
    @{
        name = $service
        status = if ($item) { $item.Status.ToString() } else { "Missing" }
    }
}

$failedServices = @($serviceStates | Where-Object { $_.status -ne "Running" }).Count
$uri = [System.Uri]$Endpoint
$checks = @(
    Test-HttpEndpoint -Url $Endpoint
    Test-DnsResolution -Hostname $uri.Host
    Test-TcpConnectivity -Hostname $uri.Host -Port 443
)

$payload = @{
    hostname = $env:COMPUTERNAME
    os = (Get-CimInstance -ClassName Win32_OperatingSystem).Caption
    cpu_percent = $cpu
    memory_percent = $memory
    failed_services = $failedServices
    services = $serviceStates
    checks = $checks
    thresholds = @{
        cpu_warn_percent = $CpuWarnPercent
        memory_warn_percent = $MemoryWarnPercent
    }
}

$json = $payload | ConvertTo-Json -Depth 8
Write-Host $json
Invoke-RestMethod -Method Post -Uri $ApiUrl -Body $json -ContentType "application/json"

