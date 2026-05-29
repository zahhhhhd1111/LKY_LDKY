$ErrorActionPreference = "Stop"
$outputFile = "c:\4code\3lot\xlsx_output.txt"

try {
    $python = "c:\4code\.venv\Scripts\python.exe"
    $script = "c:\4code\3lot\read_xlsx.py"

    # Check if python exists
    if (-not (Test-Path $python)) {
        "ERROR: Python not found at $python" | Out-File -FilePath $outputFile
        exit 1
    }

    # Run the python script and capture output
    $result = & $python $script 2>&1
    $result | Out-File -FilePath $outputFile
    exit 0
} catch {
    "EXCEPTION: $_" | Out-File -FilePath $outputFile
    exit 1
}
