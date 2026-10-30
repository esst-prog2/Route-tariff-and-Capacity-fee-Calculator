# Fills the Capacity Fee Workbook's named inputs in Excel and reads its named results.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tests/excel_check.ps1 <cases.json> <results.json>
#
# cases.json: {"workbook": "<path>", "cases": [{"inputs": {"in_booking": "Bundled", ...}, "read": ["out1_total", ...]}]}
# Inputs are set in the order given (null clears the cell); each case is recalculated, then every
# name in "read" is returned: a single value, or a list for a range (Excel errors come back as numbers
# below -2146826000). Excel runs invisibly on a temporary copy and is always closed.
param([Parameter(Mandatory)] [string] $CasesPath, [Parameter(Mandatory)] [string] $ResultsPath)

$ErrorActionPreference = "Stop"
$spec = Get-Content -Raw -Encoding UTF8 $CasesPath | ConvertFrom-Json
$copy = Join-Path ([IO.Path]::GetTempPath()) ("fee_workbook_check_" + [Guid]::NewGuid().ToString("N") + ".xlsx")
Copy-Item $spec.workbook $copy

function Read-Name($workbook, $sheet, [string] $name) {
    try {
        $value = $workbook.Names.Item($name).RefersToRange.Value2
    } catch {
        $value = $sheet.Evaluate($name)  # a name that is a formula (OFFSET), not a fixed range
        if ($value -is [__ComObject]) { $value = $value.Value2 }
    }
    if ($value -is [Array]) {
        $list = @()
        foreach ($item in $value) { $list += , $item }  # row by row for one-column ranges
        return , $list
    }
    return $value
}

$excel = New-Object -ComObject Excel.Application
try {
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.ScreenUpdating = $false
    $workbook = $excel.Workbooks.Open($copy)
    $sheet = $workbook.Worksheets.Item("Calculator")
    $excel.Calculation = -4135  # manual: one recalculation per case
    $results = @()
    foreach ($case in $spec.cases) {
        foreach ($entry in $case.inputs.PSObject.Properties) {
            $cell = $workbook.Names.Item($entry.Name).RefersToRange
            # COM takes plain strings and doubles, not the wrapped values ConvertFrom-Json gives.
            $value = $entry.Value
            if ($null -eq $value) { [void]$cell.ClearContents() }
            elseif ($value -is [string]) { $cell.Value2 = $value.PSObject.BaseObject.ToString() }
            else { $cell.Value2 = [double]$value.PSObject.BaseObject }
        }
        $excel.Calculate()
        $values = [ordered]@{}
        foreach ($name in $case.read) { $values[$name] = Read-Name $workbook $sheet $name }
        $results += , $values
    }
    $output = [ordered]@{ decimal = $excel.International(3); results = $results }
    $json = ConvertTo-Json $output -Depth 6 -Compress
    [IO.File]::WriteAllText($ResultsPath, $json, (New-Object Text.UTF8Encoding $false))
} finally {
    if ($workbook) { $workbook.Close($false) }
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    [GC]::Collect()
    Remove-Item $copy -ErrorAction SilentlyContinue
}
