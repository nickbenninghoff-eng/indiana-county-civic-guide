param([string]$Dir, [string]$OutFile)
# OCR every PNG in $Dir with the built-in Windows.Media.Ocr engine (Windows 10/11, no install).
# Writes one tab-separated row per recognized word: file, line number, x, y, width, height, text.
# Used by tools/ocr_2020_precinct_report.py (positions are needed to rebuild the report's two-column tables).
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(); $task.Result }
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$rows = New-Object System.Collections.Generic.List[string]
Get-ChildItem $Dir -Filter *.png | Sort-Object Name | ForEach-Object {
  $f = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($_.FullName)) ([Windows.Storage.StorageFile])
  $s = Await ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $r = Await ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
  $ln = 0
  foreach ($line in $r.Lines) {
    $ln++
    foreach ($w in $line.Words) {
      $b = $w.BoundingRect
      $rows.Add(("{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}" -f $_.Name, $ln, [int]$b.X, [int]$b.Y, [int]$b.Width, [int]$b.Height, $w.Text))
    }
  }
  $s.Dispose()
}
[System.IO.File]::WriteAllLines($OutFile, $rows)
