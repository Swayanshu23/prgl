# =============================================================================
# Tesseract OCR + All Indian State Languages Setup Script
# Run as Administrator in PowerShell:
#   Set-ExecutionPolicy Bypass -Scope Process -Force
#   .\setup_tesseract.ps1
# =============================================================================

$TESSDATA_DIR = "C:\Program Files\Tesseract-OCR\tessdata"
$BASE_URL     = "https://github.com/tesseract-ocr/tessdata/raw/main"

# Indian state languages available in official tessdata
# Language Code -> Description
$INDIAN_LANGS = [ordered]@{
    "hin" = "Hindi          (most states - Devanagari script)"
    "ben" = "Bengali        (West Bengal, Tripura, Jharkhand)"
    "tel" = "Telugu         (Andhra Pradesh, Telangana)"
    "mar" = "Marathi        (Maharashtra, Goa)"
    "tam" = "Tamil          (Tamil Nadu, Puducherry)"
    "urd" = "Urdu           (J&K, Telangana, UP, Bihar)"
    "guj" = "Gujarati       (Gujarat, Dadra & NH, Daman & Diu)"
    "kan" = "Kannada        (Karnataka)"
    "mal" = "Malayalam      (Kerala, Lakshadweep, Puducherry)"
    "ori" = "Odia           (Odisha)"
    "pan" = "Punjabi        (Punjab, Chandigarh, Delhi)"
    "asm" = "Assamese       (Assam)"
    "san" = "Sanskrit       (classical / Devanagari)"
    "nep" = "Nepali         (Sikkim)"
    "mai" = "Maithili       (Bihar, Jharkhand)"
    "eng" = "English        (all UTs, Meghalaya, Nagaland, Mizoram, Arunachal)"
}

# ---------------------------------------------------------------------------
# Step 1: Install Tesseract via winget (if not already installed)
# ---------------------------------------------------------------------------
Write-Host "`n[1/3] Checking Tesseract installation..." -ForegroundColor Cyan

$tessExe = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (Test-Path $tessExe) {
    Write-Host "  Tesseract already installed." -ForegroundColor Green
} else {
    Write-Host "  Installing Tesseract via winget..." -ForegroundColor Yellow
    winget install --id UB-Mannheim.TesseractOCR --silent --accept-package-agreements --accept-source-agreements
    if (-not (Test-Path $tessExe)) {
        Write-Host "  ERROR: Tesseract install failed. Download manually from:" -ForegroundColor Red
        Write-Host "  https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Tesseract installed successfully." -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# Step 2: Download all Indian language .traineddata files
# ---------------------------------------------------------------------------
Write-Host "`n[2/3] Downloading Indian language packs to:" -ForegroundColor Cyan
Write-Host "  $TESSDATA_DIR`n"

foreach ($lang in $INDIAN_LANGS.Keys) {
    $dest = Join-Path $TESSDATA_DIR "$lang.traineddata"
    $desc = $INDIAN_LANGS[$lang]

    if (Test-Path $dest) {
        Write-Host "  [SKIP]  $lang  - $desc (already exists)" -ForegroundColor DarkGray
        continue
    }

    $url = "$BASE_URL/$lang.traineddata"
    Write-Host "  [DL]    $lang  - $desc" -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -ErrorAction Stop
        Write-Host "          -> OK" -ForegroundColor Green
    } catch {
        Write-Host "          -> FAILED: $_" -ForegroundColor Red
    }
}

# ---------------------------------------------------------------------------
# Step 3: Verify
# ---------------------------------------------------------------------------
Write-Host "`n[3/3] Installed languages:" -ForegroundColor Cyan
& $tessExe --list-langs 2>&1 | ForEach-Object { Write-Host "  $_" }

Write-Host "`nDone! Add Tesseract to PATH if not already present:" -ForegroundColor Green
Write-Host '  [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\Tesseract-OCR", "Machine")' -ForegroundColor DarkGray
