# Windows Task Scheduler Setup Script
# Run this in PowerShell as Administrator

param(
    [string]$DeviceId = "tracker01",
    [string]$Time = "18:30",
    [int]$Days = 7,
    [string]$ProjectPath = "E:\Solar Tracker",
    [string]$PythonExe = "E:\Solar Tracker\venv\Scripts\python.exe",
    [string]$LogPath = "E:\Solar Tracker\logs\retrain.log"
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "Setting up Windows Task Scheduler for Model Retraining" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  Device ID: $DeviceId"
Write-Host "  Schedule Time: $Time"
Write-Host "  Training Days: $Days"
Write-Host "  Project Path: $ProjectPath"
Write-Host "  Python: $PythonExe"
Write-Host "  Log Path: $LogPath"
Write-Host ""

# Verify paths exist
if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python executable not found: $PythonExe" -ForegroundColor Red
    Write-Host "Please update the -PythonExe parameter with correct path" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path "$ProjectPath\tools\retrain_worker.py")) {
    Write-Host "ERROR: retrain_worker.py not found in: $ProjectPath\tools" -ForegroundColor Red
    exit 1
}

# Create logs directory if it doesn't exist
$LogDir = Split-Path -Parent $LogPath
if (-not (Test-Path $LogDir)) {
    Write-Host "Creating logs directory: $LogDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

Write-Host "Paths verified successfully" -ForegroundColor Green
Write-Host ""

# Task name
$TaskName = "SolarModelRetraining"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task '$TaskName' already exists. Do you want to replace it?" -ForegroundColor Yellow
    $response = Read-Host "Type 'yes' to continue"
    if ($response -ne "yes") {
        Write-Host "Aborted." -ForegroundColor Red
        exit 1
    }
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create scheduled task action
$WorkingDir = "$ProjectPath\tools"
$Arguments = "retrain_worker.py --device $DeviceId --days $Days"
$LogRedirect = ">> `"$LogPath`" 2>&1"

# Note: Task Scheduler doesn't support output redirection directly
# We need to use cmd.exe as wrapper
$CmdArguments = "/c `"cd /d `"$WorkingDir`" && `"$PythonExe`" $Arguments >> `"$LogPath`" 2>&1`""

$Action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument $CmdArguments `
    -WorkingDirectory $WorkingDir

# Create trigger (daily at specified time)
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# Register the task
Write-Host "Registering scheduled task..." -ForegroundColor Green

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Daily ML model retraining for solar tracker at $Time" `
        -User "SYSTEM" `
        -RunLevel Highest `
        -Force | Out-Null
    
    Write-Host "SUCCESS: Task registered!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "ERROR: Failed to register task: $_" -ForegroundColor Red
    exit 1
}

# Verify task was created
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($task) {
    Write-Host "Task Status:" -ForegroundColor Cyan
    Write-Host "  Name: $($task.TaskName)"
    Write-Host "  State: $($task.State)"
    Write-Host "  Next Run: $(($task | Get-ScheduledTaskInfo).NextRunTime)"
    Write-Host ""
    
    # Show task details
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Command: cmd.exe"
    Write-Host "  Arguments: $CmdArguments"
    Write-Host "  Working Directory: $WorkingDir"
    Write-Host "  Schedule: Daily at $Time"
    Write-Host "  Log File: $LogPath"
    Write-Host ""
    
    # Test run option
    Write-Host "Do you want to run a test now?" -ForegroundColor Yellow
    Write-Host "(This will execute the retraining script immediately)" -ForegroundColor Yellow
    $testRun = Read-Host "Type 'yes' to test now"
    
    if ($testRun -eq "yes") {
        Write-Host "Starting test run..." -ForegroundColor Green
        Write-Host "(Check log file for output: $LogPath)" -ForegroundColor Yellow
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 3
        
        # Show task status
        $info = Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo
        Write-Host "Task Status: $($info.LastTaskResult)" -ForegroundColor Green
        Write-Host ""
        Write-Host "View logs with:" -ForegroundColor Cyan
        Write-Host "  Get-Content `"$LogPath`" -Tail 50" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "=" -NoNewline -ForegroundColor Green
    Write-Host ("=" * 59) -ForegroundColor Green
    Write-Host "Setup Complete!" -ForegroundColor Green
    Write-Host "=" -NoNewline -ForegroundColor Green
    Write-Host ("=" * 59) -ForegroundColor Green
    Write-Host ""
    Write-Host "The task is now scheduled to run daily at $Time" -ForegroundColor Green
    Write-Host ""
    Write-Host "Useful Commands:" -ForegroundColor Cyan
    Write-Host "  View task:   Get-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Run now:     Start-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  View logs:   Get-Content `"$LogPath`" -Tail 50"
    Write-Host "  Disable:     Disable-ScheduledTask -TaskName '$TaskName'"
    Write-Host "  Remove:      Unregister-ScheduledTask -TaskName '$TaskName'"
    Write-Host ""
    Write-Host "Task Scheduler GUI: Press Win+R, type 'taskschd.msc'" -ForegroundColor Yellow
    Write-Host ""
    
} else {
    Write-Host "ERROR: Task creation failed" -ForegroundColor Red
    exit 1
}
