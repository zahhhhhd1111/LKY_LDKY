' Read ZYY字段名与属性.xlsx using VBScript and Excel COM object
Dim xlApp, xlBook, xlSheet, strFile, i, j, rowStr, fso, outFile

strFile = "c:\4code\3lot\ZYY字段名与属性.xlsx"
outFile = "c:\4code\3lot\xlsx_output_vbs.txt"

Set xlApp = CreateObject("Excel.Application")
xlApp.Visible = False
xlApp.DisplayAlerts = False

Set fso = CreateObject("Scripting.FileSystemObject")
Set outFile = fso.CreateTextFile(outFile, True)

On Error Resume Next
Set xlBook = xlApp.Workbooks.Open(strFile)
If Err.Number <> 0 Then
    outFile.WriteLine "ERROR: " & Err.Description
    outFile.Close
    WScript.Quit 1
End If
On Error GoTo 0

For Each xlSheet In xlBook.Worksheets
    outFile.WriteLine "=== Sheet: " & xlSheet.Name & " ==="
    For i = 1 To xlSheet.UsedRange.Rows.Count
        rowStr = "Row " & i & ": ["
        For j = 1 To xlSheet.UsedRange.Columns.Count
            Dim cellVal
            cellVal = xlSheet.Cells(i, j).Value
            If IsNull(cellVal) Then
                cellVal = ""
            End If
            If j > 1 Then rowStr = rowStr & ", "
            rowStr = rowStr & """" & cellVal & """"
        Next
        rowStr = rowStr & "]"
        outFile.WriteLine rowStr
    Next
    outFile.WriteLine ""
Next

xlBook.Close False
xlApp.Quit
outFile.Close

Set xlApp = Nothing
Set fso = Nothing

WScript.Echo "Done! Output written to " & outFile
