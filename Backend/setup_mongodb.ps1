# Quick MongoDB Setup Script for Windows
# Run this script to check MongoDB status and get setup instructions

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MongoDB Setup Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if MongoDB service exists
$mongoService = Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue

if ($mongoService) {
    Write-Host "✅ MongoDB service found" -ForegroundColor Green
    Write-Host "   Status: $($mongoService.Status)" -ForegroundColor White
    
    if ($mongoService.Status -eq "Running") {
        Write-Host "✅ MongoDB is running!" -ForegroundColor Green
        
        # Test connection
        Write-Host "`nTesting connection to MongoDB..." -ForegroundColor Cyan
        $connection = Test-NetConnection -ComputerName localhost -Port 27017 -WarningAction SilentlyContinue
        
        if ($connection.TcpTestSucceeded) {
            Write-Host "✅ MongoDB is accessible on port 27017" -ForegroundColor Green
            Write-Host "`n🚀 You're ready to run the API server!" -ForegroundColor Green
            Write-Host "   Run: python -m app.main" -ForegroundColor White
        } else {
            Write-Host "❌ Cannot connect to MongoDB on port 27017" -ForegroundColor Red
            Write-Host "   The service is running but not responding." -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ MongoDB service is stopped" -ForegroundColor Red
        Write-Host "`nAttempting to start MongoDB service..." -ForegroundColor Yellow
        
        try {
            Start-Service -Name "MongoDB"
            Write-Host "✅ MongoDB service started successfully!" -ForegroundColor Green
            Start-Sleep -Seconds 2
            
            $connection = Test-NetConnection -ComputerName localhost -Port 27017 -WarningAction SilentlyContinue
            if ($connection.TcpTestSucceeded) {
                Write-Host "✅ MongoDB is now accessible" -ForegroundColor Green
                Write-Host "`n🚀 You're ready to run the API server!" -ForegroundColor Green
                Write-Host "   Run: python -m app.main" -ForegroundColor White
            }
        } catch {
            Write-Host "❌ Failed to start MongoDB service" -ForegroundColor Red
            Write-Host "   You may need to run PowerShell as Administrator" -ForegroundColor Yellow
            Write-Host "`nTry running this command as Administrator:" -ForegroundColor Yellow
            Write-Host "   Start-Service -Name MongoDB" -ForegroundColor White
        }
    }
} else {
    Write-Host "❌ MongoDB is not installed on this system" -ForegroundColor Red
    Write-Host ""
    Write-Host "You have 3 options:" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Option 1: Install MongoDB locally (Recommended)" -ForegroundColor Cyan
    Write-Host "  1. Download from: https://www.mongodb.com/try/download/community" -ForegroundColor White
    Write-Host "  2. Run the installer" -ForegroundColor White
    Write-Host "  3. Make sure 'Install as Service' is checked" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Option 2: Use Docker (Easiest)" -ForegroundColor Cyan
    Write-Host "  Run: docker run -d --name mongodb-solar -p 27017:27017 mongo:latest" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Option 3: Use MongoDB Atlas (Cloud - Free)" -ForegroundColor Cyan
    Write-Host "  1. Create free account at: https://www.mongodb.com/cloud/atlas" -ForegroundColor White
    Write-Host "  2. Create a cluster" -ForegroundColor White
    Write-Host "  3. Update MONGODB_URL in .env file" -ForegroundColor White
    Write-Host ""
    
    Write-Host "For detailed instructions, see: MONGODB_SETUP.md" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Check for Docker as alternative
Write-Host "`nChecking for Docker..." -ForegroundColor Cyan
$docker = Get-Command docker -ErrorAction SilentlyContinue

if ($docker) {
    Write-Host "✅ Docker is installed" -ForegroundColor Green
    
    # Check if container exists
    $container = docker ps -a --filter "name=mongodb-solar" --format "{{.Names}}" 2>$null
    
    if ($container) {
        $status = docker ps --filter "name=mongodb-solar" --format "{{.Status}}" 2>$null
        
        if ($status) {
            Write-Host "✅ MongoDB Docker container is running" -ForegroundColor Green
        } else {
            Write-Host "⚠️  MongoDB Docker container exists but is stopped" -ForegroundColor Yellow
            Write-Host "   Start it with: docker start mongodb-solar" -ForegroundColor White
        }
    } else {
        Write-Host "ℹ️  No MongoDB Docker container found" -ForegroundColor Yellow
        Write-Host "`nYou can create one with:" -ForegroundColor Cyan
        Write-Host "docker run -d --name mongodb-solar -p 27017:27017 mongo:latest" -ForegroundColor White
    }
} else {
    Write-Host "ℹ️  Docker is not installed" -ForegroundColor Yellow
    Write-Host "   Install from: https://www.docker.com/products/docker-desktop" -ForegroundColor White
}

Write-Host ""
