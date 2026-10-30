' Arrete l'application (le serveur lance en arriere-plan par lancer.vbs).
Option Explicit

Dim fso, appDir, wmi, procs, p, n
Set fso = CreateObject("Scripting.FileSystemObject")
appDir = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
Set wmi = GetObject("winmgmts:\\.\root\cimv2")
Set procs = wmi.ExecQuery("SELECT * FROM Win32_Process WHERE Name = 'pythonw.exe' OR Name = 'python.exe'")
n = 0
For Each p In procs
    If Not IsNull(p.CommandLine) Then
        If InStr(1, p.CommandLine, appDir & "\run.py", vbTextCompare) > 0 Then
            ' Le processus enfant peut deja etre arrete avec son parent : on ignore l'erreur
            On Error Resume Next
            p.Terminate
            On Error GoTo 0
            n = n + 1
        End If
    End If
Next
If n > 0 Then
    MsgBox "Application arretee.", vbInformation, "Gestion location"
Else
    MsgBox "L'application n'etait pas en cours d'execution.", vbInformation, "Gestion location"
End If
