# scripts/wsl_portforward.ps1
# NOTE: This script must be run as Administrator!

Write-Host "Starting WSL2 Port Forwarding for UR5 ROS 2 Driver..." -ForegroundColor Cyan

# 1. Get the current WSL2 IP Address
# We use wsl.exe to run 'hostname -I' inside the Ubuntu instance to get its hidden IP.
$wsl_ip = wsl.exe -d Ubuntu-22.04 -e hostname -I
$wsl_ip = $wsl_ip.Trim().Split(' ')[0]

if (-not $wsl_ip) {
    Write-Error "Failed to retrieve WSL IP address. Is WSL running? Try running 'wsl' first."
    exit
}

Write-Host "Detected WSL IP Address: $wsl_ip" -ForegroundColor Green

# 2. Reset any existing portproxy rules to prevent conflicts
Write-Host "Resetting existing portproxy rules..."
netsh interface portproxy reset ipv4tov4

# 3. Define the ports required by Universal_Robots_ROS2_Driver
# 50001: Script Sender
# 50002: Reverse Interface (The main control port)
# 50003: Dashboard Client
# 50004: Trajectory Port
$ports = @(50001, 50002, 50003, 50004)

# 4. Create the PortProxy rules and Windows Firewall exceptions
foreach ($port in $ports) {
    Write-Host "Forwarding TCP Port $port to WSL Localhost..."
    
    # Route the traffic through Windows into WSL via the Localhost Loopback
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=127.0.0.1
    
    # Ensure Windows Firewall doesn't block the incoming robot traffic
    Remove-NetFirewallRule -DisplayName "UR5_ROS2_Port_$port" -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "UR5_ROS2_Port_$port" -Direction Inbound -Action Allow -Protocol TCP -LocalPort $port | Out-Null
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Port Forwarding Complete!" -ForegroundColor Green
Write-Host "The UR5 can now communicate with your WSL2 instance." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
