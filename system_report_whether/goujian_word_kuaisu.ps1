$ErrorActionPreference = 'Stop'

$workspace = (Get-Location).Path
$sourcePath = Join-Path $workspace 'report_source.md'
$outputPath = Join-Path $workspace '调研报告_填充排版完成版.docx'
$pdfPath = Join-Path $workspace '调研报告_排版预览.pdf'

$wdSectionBreakNextPage = 2
$wdAlignParagraphLeft = 0
$wdAlignParagraphCenter = 1
$wdAlignParagraphJustify = 3
$wdLineSpaceOnePtFive = 1
$wdFieldTOC = 13
$wdFormatDocumentDefault = 16
$wdExportFormatPDF = 17
$wdPageNumberStyleArabic = 0
$wdPageNumberStyleLowercaseRoman = 2
$wdHeaderFooterPrimary = 1

function Set-Font($range, [double]$size, [bool]$bold = $false) {
    $range.Font.Name = 'Times New Roman'
    $range.Font.NameAscii = 'Times New Roman'
    $range.Font.NameOther = 'Times New Roman'
    $range.Font.NameFarEast = '宋体'
    $range.Font.Size = $size
    $range.Font.Bold = if ($bold) { -1 } else { 0 }
}

function Format-Paragraph($paragraph, [string]$kind) {
    $pf = $paragraph.Format
    $pf.LineSpacingRule = $wdLineSpaceOnePtFive
    $pf.SpaceBefore = 0
    $pf.SpaceAfter = 0
    $pf.FirstLineIndent = 0
    $pf.LeftIndent = 0
    $pf.RightIndent = 0
    $pf.KeepTogether = 0
    $pf.KeepWithNext = 0
    $pf.WidowControl = -1
    $pf.OutlineLevel = 10

    switch ($kind) {
        'title' { Set-Font $paragraph.Range 16 $true; $pf.Alignment = $wdAlignParagraphCenter; $pf.SpaceAfter = 8; $pf.KeepWithNext = -1 }
        'subtitle' { Set-Font $paragraph.Range 16 $true; $pf.Alignment = $wdAlignParagraphCenter; $pf.SpaceAfter = 6 }
        'cover' { Set-Font $paragraph.Range 14 $false; $pf.Alignment = $wdAlignParagraphCenter; $pf.SpaceAfter = 8 }
        'toc_title' { Set-Font $paragraph.Range 16 $true; $pf.Alignment = $wdAlignParagraphCenter; $pf.SpaceAfter = 12; $pf.KeepWithNext = -1 }
        'heading1' { Set-Font $paragraph.Range 14 $true; $pf.Alignment = $wdAlignParagraphLeft; $pf.SpaceBefore = 12; $pf.SpaceAfter = 6; $pf.KeepWithNext = -1; $pf.OutlineLevel = 1 }
        'heading2' { Set-Font $paragraph.Range 12 $true; $pf.Alignment = $wdAlignParagraphLeft; $pf.SpaceBefore = 6; $pf.SpaceAfter = 3; $pf.KeepWithNext = -1; $pf.OutlineLevel = 2 }
        'reference' { Set-Font $paragraph.Range 10.5 $false; $pf.Alignment = $wdAlignParagraphJustify; $pf.LeftIndent = 24; $pf.FirstLineIndent = -24; $pf.SpaceAfter = 3 }
        'appendix' { Set-Font $paragraph.Range 12 $false; $pf.Alignment = $wdAlignParagraphJustify; $pf.LeftIndent = 24; $pf.FirstLineIndent = -24 }
        'keywords' { Set-Font $paragraph.Range 12 $false; $pf.Alignment = $wdAlignParagraphJustify; $pf.FirstLineIndent = 0; if ($paragraph.Range.Characters.Count -gt 3) { $paragraph.Range.Characters.Item(1).Font.Bold = -1 } }
        default { Set-Font $paragraph.Range 12 $false; $pf.Alignment = $wdAlignParagraphJustify; $pf.FirstLineIndent = 24 }
    }
}

function Append-Part($document, [string[]]$lines, [string[]]$kinds) {
    $text = (($lines -join "`r") + "`r")
    $start = $document.Content.End - 1
    $insert = $document.Range($start, $start)
    $insert.InsertAfter($text)
    $partRange = $document.Range($start, $start + $text.Length)
    $parts = $partRange.Paragraphs
    for ($i = 1; $i -le $kinds.Count; $i++) {
        Format-Paragraph $parts.Item($i) $kinds[$i - 1]
    }
    return $partRange
}

function Add-PageNumber($section, [int]$style) {
    $section.Headers.Item($wdHeaderFooterPrimary).LinkToPrevious = $false
    $section.Footers.Item($wdHeaderFooterPrimary).LinkToPrevious = $false
    $footer = $section.Footers.Item($wdHeaderFooterPrimary).Range
    $footer.Text = ''
    $footer.ParagraphFormat.Alignment = $wdAlignParagraphCenter
    Set-Font $footer 10.5 $false
    $section.Footers.Item($wdHeaderFooterPrimary).PageNumbers.RestartNumberingAtSection = $true
    $section.Footers.Item($wdHeaderFooterPrimary).PageNumbers.StartingNumber = 1
    $section.Footers.Item($wdHeaderFooterPrimary).PageNumbers.NumberStyle = $style
    $section.Footers.Item($wdHeaderFooterPrimary).PageNumbers.Add($wdAlignParagraphCenter, $true) | Out-Null
}

$coverLines = @(
    '行走于青衣江与大巴山之间',
    '——雅安市雨城区、巴中南龛与通江王坪烈士陵园调研报告',
    '　','　','　','　','　','　',
    '学校：四川农业大学', '学院：水利水电学院', '专业：____________________',
    '班级：____________________', '姓名：____________________', '学号：____________________',
    '指导教师：________________', '　','　', '完成时间：2026年7月',
    '正文字数：约1.31万字（不含参考文献与附录）'
)
$coverKinds = @('title','subtitle','cover','cover','cover','cover','cover','cover','cover','cover','cover','cover','cover','cover','cover','cover','cover','cover','cover')

$bodyLines = New-Object System.Collections.Generic.List[string]
$bodyKinds = New-Object System.Collections.Generic.List[string]

$inReferences = $false; $inAppendix = $false
foreach ($raw in (Get-Content -LiteralPath $sourcePath -Encoding UTF8)) {
    $text = $raw.Trim()
    if ([string]::IsNullOrWhiteSpace($text) -or $text.StartsWith('# ')) { continue }
    if ($text.StartsWith('## ')) { $h = $text.Substring(3); $inReferences = ($h -eq '参考文献'); $inAppendix = $h.StartsWith('附录'); $bodyLines.Add($h); $bodyKinds.Add('heading1'); continue }
    if ($text.StartsWith('### ')) { $bodyLines.Add($text.Substring(4)); $bodyKinds.Add('heading2'); continue }
    if ($inReferences -and $text.StartsWith('[')) { $bodyLines.Add($text); $bodyKinds.Add('reference'); continue }
    if ($inAppendix -and $text -match '^\d+\.') { $bodyLines.Add($text); $bodyKinds.Add('appendix'); continue }
    if ($text.StartsWith('关键词：')) { continue }
    $bodyLines.Add($text); $bodyKinds.Add('body')
}

$word = $null; $document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.ScreenUpdating = $false
    $document = $word.Documents.Add()
    $document.Content.Delete()

    [void](Append-Part $document $coverLines $coverKinds)
    $range = $document.Range($document.Content.End - 1, $document.Content.End - 1)
    $range.InsertBreak($wdSectionBreakNextPage)

    $tocText = @('目录', '目录字段将在更新后显示')
    $tocKinds = @('toc_title', 'body')
    $tocRange = Append-Part $document $tocText $tocKinds
    $fieldRange = $tocRange.Paragraphs.Item(2).Range
    $fieldRange.Text = ''
    $document.Fields.Add($fieldRange, $wdFieldTOC, 'TOC \o "1-2" \h \z \u', $true) | Out-Null
    $range = $document.Range($document.Content.End - 1, $document.Content.End - 1)
    $range.InsertBreak($wdSectionBreakNextPage)

    [void](Append-Part $document $bodyLines.ToArray() $bodyKinds.ToArray())

    foreach ($section in $document.Sections) {
        $section.PageSetup.TopMargin = 72
        $section.PageSetup.BottomMargin = 72
        $section.PageSetup.LeftMargin = 90
        $section.PageSetup.RightMargin = 72
    }
    $document.Sections.Item(1).Footers.Item($wdHeaderFooterPrimary).Range.Text = ''
    Add-PageNumber $document.Sections.Item(2) $wdPageNumberStyleLowercaseRoman
    Add-PageNumber $document.Sections.Item(3) $wdPageNumberStyleArabic

    $document.Fields.Update() | Out-Null
    $document.Repaginate()
    $document.SaveAs2($outputPath, $wdFormatDocumentDefault)
    $document.ExportAsFixedFormat($pdfPath, $wdExportFormatPDF)

    [pscustomobject]@{ Output=$outputPath; PdfPreview=$pdfPath; Pages=$document.ComputeStatistics(2); Characters=$document.ComputeStatistics(3); Paragraphs=$document.Paragraphs.Count; Sections=$document.Sections.Count } | Format-List
}
finally {
    if ($document -ne $null) { $document.Close($false); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($document) }
    if ($word -ne $null) { $word.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
