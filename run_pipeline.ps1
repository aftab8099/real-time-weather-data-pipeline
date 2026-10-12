
$ProjectDir = "C:\Users\Aftab Alam\Desktop\real-time-weather-data-pipeline"
$PythonExe = "$ProjectDir\venv\Scripts\python.exe"
$LogDir = "$ProjectDir\logs"

New-Item -ItemType Directory -Force $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "pipeline_$Timestamp.log"

Set-Location $ProjectDir

"Pipeline started at $(Get-Date)" | Out-File $LogFile -Encoding utf8

& $PythonExe -m src.pipeline 2>&1 |
    ForEach-Object {
        "$_" | Out-File $LogFile -Append -Encoding utf8
        Write-Host "$_"
    }

$PipelineExitCode = $LASTEXITCODE

if ($PipelineExitCode -ne 0) {
    "Pipeline failed at $(Get-Date)" | Out-File $LogFile -Append -Encoding utf8
    exit $PipelineExitCode
}

"Pipeline completed at $(Get-Date)" | Out-File $LogFile -Append -Encoding utf8
Write-Host "Pipeline succeeded. Log saved to: $LogFile"
