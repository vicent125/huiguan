$ErrorActionPreference = 'Stop'

$workspace = (Get-Location).Path
$sourcePath = Join-Path $workspace 'report_source.md'
$templatePath = 'C:\Users\D1782\Desktop\调研报告.docx'
$outputPath = Join-Path $workspace '调研报告_填充排版完成版.docx'
$pdfPath = Join-Path $workspace '调研报告_排版预览.pdf'

$wdCollapseEnd = 0
$wdPageBreak = 7
$wdSectionBreakNextPage = 2
$wdAlignParagraphLeft = 0
$wdAlignParagraphCenter = 1
$wdAlignParagraphJustify = 3
$wdLineSpaceOnePtFive = 1
$wdOutlineLevelBodyText = 10
$wdPageNumberStyleArabic = 0
$wdPageNumberStyleLowercaseRoman = 2
$wdHeaderFooterPrimary = 1
$wdFormatDocumentDefault = 16
$wdExportFormatPDF = 17
$wdPaperA4 = 7

function Set-RunFont {
    param(
        [Parameter(Mandatory = $true)] $Range,
        [double] $Size,
        [bool] $Bold = $false
    )
    $Range.Font.Name = 'Times New Roman'
    $Range.Font.NameAscii = 'Times New Roman'
    $Range.Font.NameOther = 'Times New Roman'
    $Range.Font.NameFarEast = '宋体'
    $Range.Font.Size = $Size
    $Range.Font.Bold = if ($Bold) { -1 } else { 0 }
}

function Add-Paragraph {
    param(
        [Parameter(Mandatory = $true)] $Document,
        [Parameter(Mandatory = $true)] [string] $Text,
        [Parameter(Mandatory = $true)] [ValidateSet('Title', 'Subtitle', 'Cover', 'TocTitle', 'Heading1', 'Heading2', 'Body', 'Keywords', 'Reference', 'AppendixItem')] [string] $Kind
    )

    $insert = $Document.Range($Document.Content.End - 1, $Document.Content.End - 1)
    $insert.InsertAfter($Text)
    $insert.InsertParagraphAfter()
    $paragraph = $Document.Paragraphs.Item($Document.Paragraphs.Count - 1)
    $format = $paragraph.Format

    $format.SpaceBefore = 0
    $format.SpaceAfter = 0
    $format.LineSpacingRule = $wdLineSpaceOnePtFive
    $format.KeepTogether = 0
    $format.KeepWithNext = 0
    $format.WidowControl = -1
    $format.FirstLineIndent = 0
    $format.LeftIndent = 0
    $format.RightIndent = 0
    $format.OutlineLevel = $wdOutlineLevelBodyText

    switch ($Kind) {
        'Title' {
            Set-RunFont -Range $paragraph.Range -Size 16 -Bold $true
            $format.Alignment = $wdAlignParagraphCenter
            $format.SpaceAfter = 8
            $format.LineSpacingRule = $wdLineSpaceOnePtFive
        }
        'Subtitle' {
            Set-RunFont -Range $paragraph.Range -Size 16 -Bold $true
            $format.Alignment = $wdAlignParagraphCenter
            $format.SpaceAfter = 6
        }
        'Cover' {
            Set-RunFont -Range $paragraph.Range -Size 14 -Bold $false
            $format.Alignment = $wdAlignParagraphCenter
            $format.SpaceAfter = 8
        }
        'TocTitle' {
            Set-RunFont -Range $paragraph.Range -Size 16 -Bold $true
            $format.Alignment = $wdAlignParagraphCenter
            $format.SpaceAfter = 12
        }
        'Heading1' {
            Set-RunFont -Range $paragraph.Range -Size 14 -Bold $true
            $format.Alignment = $wdAlignParagraphLeft
            $format.SpaceBefore = 12
            $format.SpaceAfter = 6
            $format.KeepWithNext = -1
            $format.OutlineLevel = 1
        }
        'Heading2' {
            Set-RunFont -Range $paragraph.Range -Size 12 -Bold $true
            $format.Alignment = $wdAlignParagraphLeft
            $format.SpaceBefore = 6
            $format.SpaceAfter = 3
            $format.KeepWithNext = -1
            $format.OutlineLevel = 2
        }
        'Body' {
            Set-RunFont -Range $paragraph.Range -Size 12 -Bold $false
            $format.Alignment = $wdAlignParagraphJustify
            $format.FirstLineIndent = 24
        }
        'Keywords' {
            Set-RunFont -Range $paragraph.Range -Size 12 -Bold $false
            $format.Alignment = $wdAlignParagraphJustify
            $format.FirstLineIndent = 0
            $paragraph.Range.Characters.Item(1).Font.Bold = -1
            if ($paragraph.Range.Characters.Count -ge 4) {
                $keyRange = $Document.Range($paragraph.Range.Start, $paragraph.Range.Start + 3)
                $keyRange.Font.Bold = -1
            }
        }
        'Reference' {
            Set-RunFont -Range $paragraph.Range -Size 10.5 -Bold $false
            $format.Alignment = $wdAlignParagraphJustify
            $format.LeftIndent = 24
            $format.FirstLineIndent = -24
            $format.SpaceAfter = 3
        }
        'AppendixItem' {
            Set-RunFont -Range $paragraph.Range -Size 12 -Bold $false
            $format.Alignment = $wdAlignParagraphJustify
            $format.FirstLineIndent = 0
            $format.LeftIndent = 24
            $format.FirstLineIndent = -24
        }
    }

    return $paragraph
}

function Add-BlankLines {
    param($Document, [int] $Count)
    for ($i = 0; $i -lt $Count; $i++) {
        $p = Add-Paragraph -Document $Document -Text ' ' -Kind 'Cover'
        $p.Range.Font.Size = 12
    }
}

function Add-SectionBreak {
    param($Document)
    $range = $Document.Range($Document.Content.End - 1, $Document.Content.End - 1)
    $range.InsertBreak($wdSectionBreakNextPage)
}

function Configure-Page {
    param($Section)
    $Section.PageSetup.PaperSize = $wdPaperA4
    $Section.PageSetup.TopMargin = 72
    $Section.PageSetup.BottomMargin = 72
    $Section.PageSetup.LeftMargin = 90
    $Section.PageSetup.RightMargin = 72
    $Section.PageSetup.HeaderDistance = 36
    $Section.PageSetup.FooterDistance = 36
}

$word = $null
$document = $null

try {
    Write-Output 'stage: start-word'
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.ScreenUpdating = $false
    $word.Options.Pagination = $false

    $document = $word.Documents.Open($templatePath, $false, $false)
    Write-Output 'stage: opened-template'
    $document.Content.Delete()

    $title = Add-Paragraph -Document $document -Text '行走于青衣江与大巴山之间' -Kind 'Title'
    $subtitle = Add-Paragraph -Document $document -Text '——雅安市雨城区、巴中南龛与通江王坪烈士陵园调研报告' -Kind 'Subtitle'
    Add-BlankLines -Document $document -Count 7
    Add-Paragraph -Document $document -Text '学校：四川农业大学' -Kind 'Cover' | Out-Null
    Add-Paragraph -Document $document -Text '学院：水利水电学院' -Kind 'Cover' | Out-Null
    Add-Paragraph -Document $document -Text '专业：____________________' -Kind 'Cover' | Out-Null
    Add-Paragraph -Document $document -Text '班级：____________________' -Kind 'Cover' | Out-Null
    Add-Paragraph -Document $document -Text '姓名：____________________' -Kind 'Cover' | Out-Null
    Add-Paragraph -Document $document -Text '学号：____________________' -Kind 'Cover' | Out-Null
    Add-Paragraph -Document $document -Text '指导教师：________________' -Kind 'Cover' | Out-Null
    Add-BlankLines -Document $document -Count 2
    Add-Paragraph -Document $document -Text '完成时间：2026年7月' -Kind 'Cover' | Out-Null
    Add-Paragraph -Document $document -Text '正文字数：约1.31万字（不含参考文献与附录）' -Kind 'Cover' | Out-Null
    Write-Output 'stage: cover-complete'

    Add-SectionBreak -Document $document
    Add-Paragraph -Document $document -Text '目录' -Kind 'TocTitle' | Out-Null
    $tocRange = $document.Range($document.Content.End - 1, $document.Content.End - 1)
    $toc = $document.TablesOfContents.Add($tocRange, $false, 1, 2, $false, '', $true, $true, '', $true, $true, $true)
    $afterToc = $document.Range($document.Content.End - 1, $document.Content.End - 1)
    $afterToc.InsertParagraphAfter()
    Write-Output 'stage: toc-placeholder-complete'

    Add-SectionBreak -Document $document

    $lines = Get-Content -LiteralPath $sourcePath -Encoding UTF8
    $inReferences = $false
    $inAppendix = $false
    $lineNumber = 0
    foreach ($line in $lines) {
        $lineNumber++
        if (($lineNumber % 20) -eq 0) {
            Write-Output ('stage: content-line-' + $lineNumber)
        }
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) {
            continue
        }
        if ($trimmed.StartsWith('# ')) {
            continue
        }
        if ($trimmed.StartsWith('## ')) {
            $heading = $trimmed.Substring(3)
            $inReferences = ($heading -eq '参考文献')
            $inAppendix = $heading.StartsWith('附录')
            Add-Paragraph -Document $document -Text $heading -Kind 'Heading1' | Out-Null
            continue
        }
        if ($trimmed.StartsWith('### ')) {
            Add-Paragraph -Document $document -Text $trimmed.Substring(4) -Kind 'Heading2' | Out-Null
            continue
        }

        if ($inReferences -and $trimmed.StartsWith('[')) {
            Add-Paragraph -Document $document -Text $trimmed -Kind 'Reference' | Out-Null
        }
        elseif ($inAppendix -and $trimmed -match '^\d+\.') {
            Add-Paragraph -Document $document -Text $trimmed -Kind 'AppendixItem' | Out-Null
        }
        elseif ($trimmed.StartsWith('关键词：')) {
            Add-Paragraph -Document $document -Text $trimmed -Kind 'Keywords' | Out-Null
        }
        else {
            Add-Paragraph -Document $document -Text $trimmed -Kind 'Body' | Out-Null
        }
    }
    Write-Output 'stage: content-complete'

    foreach ($section in $document.Sections) {
        Configure-Page -Section $section
    }
    Write-Output 'stage: page-setup-complete'

    # Cover page: no header or page number.
    $document.Sections.Item(1).Headers.Item($wdHeaderFooterPrimary).Range.Text = ''
    $document.Sections.Item(1).Footers.Item($wdHeaderFooterPrimary).Range.Text = ''

    # Contents: Roman numerals.
    $contentsSection = $document.Sections.Item(2)
    $contentsSection.Headers.Item($wdHeaderFooterPrimary).LinkToPrevious = $false
    $contentsSection.Footers.Item($wdHeaderFooterPrimary).LinkToPrevious = $false
    $contentsHeader = $contentsSection.Headers.Item($wdHeaderFooterPrimary).Range
    $contentsHeader.Text = '四川农业大学水利水电学院思想政治理论课社会实践调研报告'
    Set-RunFont -Range $contentsHeader -Size 9 -Bold $false
    $contentsHeader.ParagraphFormat.Alignment = $wdAlignParagraphCenter
    $contentsSection.Footers.Item($wdHeaderFooterPrimary).PageNumbers.RestartNumberingAtSection = $true
    $contentsSection.Footers.Item($wdHeaderFooterPrimary).PageNumbers.StartingNumber = 1
    $contentsSection.Footers.Item($wdHeaderFooterPrimary).PageNumbers.NumberStyle = $wdPageNumberStyleLowercaseRoman
    $contentsSection.Footers.Item($wdHeaderFooterPrimary).PageNumbers.Add($wdAlignParagraphCenter, $true) | Out-Null

    # Main text: Arabic numerals restart at 1.
    $mainSection = $document.Sections.Item(3)
    $mainSection.Headers.Item($wdHeaderFooterPrimary).LinkToPrevious = $false
    $mainSection.Footers.Item($wdHeaderFooterPrimary).LinkToPrevious = $false
    $mainHeader = $mainSection.Headers.Item($wdHeaderFooterPrimary).Range
    $mainHeader.Text = '四川农业大学水利水电学院思想政治理论课社会实践调研报告'
    Set-RunFont -Range $mainHeader -Size 9 -Bold $false
    $mainHeader.ParagraphFormat.Alignment = $wdAlignParagraphCenter
    $mainSection.Footers.Item($wdHeaderFooterPrimary).PageNumbers.RestartNumberingAtSection = $true
    $mainSection.Footers.Item($wdHeaderFooterPrimary).PageNumbers.StartingNumber = 1
    $mainSection.Footers.Item($wdHeaderFooterPrimary).PageNumbers.NumberStyle = $wdPageNumberStyleArabic
    $mainSection.Footers.Item($wdHeaderFooterPrimary).PageNumbers.Add($wdAlignParagraphCenter, $true) | Out-Null
    Write-Output 'stage: headers-footers-complete'

    $toc.Update()
    Write-Output 'stage: toc-updated'
    Set-RunFont -Range $toc.Range -Size 12 -Bold $false
    $toc.Range.ParagraphFormat.LineSpacingRule = $wdLineSpaceOnePtFive
    $toc.Range.ParagraphFormat.SpaceAfter = 3

    $document.Fields.Update() | Out-Null
    $word.Options.Pagination = $true
    $document.Repaginate()
    Write-Output 'stage: repaginated'

    $document.SaveAs2($outputPath, $wdFormatDocumentDefault)
    Write-Output 'stage: docx-saved'
    $document.ExportAsFixedFormat($pdfPath, $wdExportFormatPDF)
    Write-Output 'stage: pdf-saved'

    $stats = [pscustomobject]@{
        Output = $outputPath
        PdfPreview = $pdfPath
        Pages = $document.ComputeStatistics(2)
        Characters = $document.ComputeStatistics(3)
        CharactersWithSpaces = $document.ComputeStatistics(5)
        Paragraphs = $document.Paragraphs.Count
        Sections = $document.Sections.Count
    }
    $stats | Format-List
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
