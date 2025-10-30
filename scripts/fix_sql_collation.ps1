# PowerShell script to fix MySQL collation in SQL files
# Usage: .\fix_sql_collation.ps1 input.sql output.sql

param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputFile
)

Write-Host "Fixing collation in SQL file..."
Write-Host "Input: $InputFile"
Write-Host "Output: $OutputFile"

# Read the file and replace the collation
$content = Get-Content $InputFile -Raw
$newContent = $content -replace 'utf8mb4_0900_ai_ci', 'utf8mb4_unicode_ci'
$newContent = $newContent -replace 'utf8mb4_0900_as_ci', 'utf8mb4_unicode_ci'
$newContent = $newContent -replace 'utf8mb4_0900_as_cs', 'utf8mb4_unicode_ci'

# Save to output file
$newContent | Set-Content -Path $OutputFile

Write-Host "✅ Done! Fixed SQL file saved to: $OutputFile"
Write-Host ""
Write-Host "Changes made:"
Write-Host "  - utf8mb4_0900_ai_ci → utf8mb4_unicode_ci"
Write-Host ""
Write-Host "You can now import: $OutputFile"
