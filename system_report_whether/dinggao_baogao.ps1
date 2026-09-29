$ErrorActionPreference = 'Stop'

$workspace = (Get-Location).Path
$docxPath = Join-Path $workspace '调研报告_填充排版完成版.docx'
$pdfPath = Join-Path $workspace '调研报告_排版预览.pdf'
$wdExportFormatPDF = 17
$wdLineSpaceOnePtFive = 1

$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.ScreenUpdating = $false

    # OpenAndRepair lets Word normalize the generated Open XML package if its
    # template-specific metadata is stricter than the standard schema.
    $document = $word.Documents.Open($docxPath, $false, $false, $false, '', '', $false, '', '', 16, $null, $false, $true)
    $document.Fields.Update() | Out-Null
    if ($document.TablesOfContents.Count -gt 0) {
        $toc = $document.TablesOfContents.Item(1)
        $toc.Update()
        $toc.Range.Font.Name = 'Times New Roman'
        $toc.Range.Font.NameAscii = 'Times New Roman'
        $toc.Range.Font.NameOther = 'Times New Roman'
        $toc.Range.Font.NameFarEast = '宋体'
        $toc.Range.Font.Size = 12
        $toc.Range.ParagraphFormat.LineSpacingRule = $wdLineSpaceOnePtFive
        $toc.Range.ParagraphFormat.SpaceAfter = 3
    }

    $document.Repaginate()
    $document.Save()
    $document.ExportAsFixedFormat($pdfPath, $wdExportFormatPDF)

    [pscustomobject]@{
        Output = $docxPath
        PdfPreview = $pdfPath
        Pages = $document.ComputeStatistics(2)
        Characters = $document.ComputeStatistics(3)
        CharactersWithSpaces = $document.ComputeStatistics(5)
        Paragraphs = $document.Paragraphs.Count
        Sections = $document.Sections.Count
        TocEntries = if ($document.TablesOfContents.Count -gt 0) { $document.TablesOfContents.Item(1).Range.Paragraphs.Count } else { 0 }
    } | Format-List
}
finally {
    if ($document -ne $null) {
        $document.Close($false)
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document)
    }
    if ($word -ne $null) {
        $word.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
