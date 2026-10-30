' Lance l'application en arriere-plan (sans fenetre noire) et ouvre le navigateur.
' Si l'application tourne deja, ouvre seulement le navigateur.
Option Explicit

Const URL = "http://127.0.0.1:5000/"

Dim sh, fso, appDir, pythonw, i
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
appDir = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
pythonw = appDir & "\.venv\Scripts\pythonw.exe"

Function AppRepond()
    Dim http
    AppRepond = False
    On Error Resume Next
    Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
    http.setTimeouts 1000, 1000, 2000, 2000
    http.Open "GET", URL, False
    http.Send
    If Err.Number = 0 Then
        If http.Status = 200 Then AppRepond = True
    End If
    Err.Clear
    On Error GoTo 0
End Function

If Not AppRepond() Then
    If Not fso.FileExists(pythonw) Then
        MsgBox "L'application n'est pas installee." & vbCrLf & _
               "Double-cliquez d'abord sur INSTALLER.bat dans le dossier :" & vbCrLf & appDir, _
               vbExclamation, "Gestion location"
        WScript.Quit 1
    End If
    sh.CurrentDirectory = appDir
    sh.Run """" & pythonw & """ """ & appDir & "\run.py""", 0, False
    For i = 1 To 60
        WScript.Sleep 500
        If AppRepond() Then Exit For
    Next
    If Not AppRepond() Then
        MsgBox "L'application n'a pas pu demarrer." & vbCrLf & _
               "Consultez le fichier : " & appDir & "\instance\app.log", _
               vbCritical, "Gestion location"
        WScript.Quit 1
    End If
End If

sh.Run URL
