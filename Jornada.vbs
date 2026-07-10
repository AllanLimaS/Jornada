' ==========================================================================
'  Jornada - Launcher (portatil)
'  Sobe o servidor FastAPI oculto e abre em modo app (janela sem cabecalho).
'  Resolve tudo a partir da pasta onde este arquivo esta -> funciona em
'  qualquer PC que clonar o repositorio (basta ter Python 3 no PATH).
' ==========================================================================
Option Explicit

Dim sh, fso, projDir, py, logFile, url, i, cmd, browser, profile
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projDir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = projDir
py = projDir & "\.venv\Scripts\python.exe"
logFile = sh.ExpandEnvironmentStrings("%TEMP%") & "\jornada-srv.log"
url = "http://127.0.0.1:7734/"

' 1) Primeira execucao: cria o ambiente virtual e instala dependencias.
'    Mostra janela (visivel) porque pode demorar; espera terminar.
If Not fso.FileExists(py) Then
    sh.Run "cmd /c python -m venv "".venv""", 1, True
    sh.Run "cmd /c "".venv\Scripts\python.exe"" -m pip install -r requirements.txt", 1, True
End If

' 2) Sobe o servidor apenas se ainda nao estiver respondendo.
If Not ServidorNoAr(url) Then
    cmd = "cmd /c """"" & py & """ -m uvicorn main:app --port 7734 > """ & logFile & """ 2>&1"""
    sh.Run cmd, 0, False
    i = 0
    Do While (Not ServidorNoAr(url)) And (i < 30)
        WScript.Sleep 1000
        i = i + 1
    Loop
End If

' 3) Abre em modo app (Chrome/Edge). Sem navegador compativel -> navegador padrao.
browser = AcharNavegador()
profile = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\JornadaApp"
If browser <> "" Then
    sh.Run """" & browser & """ --app=" & url & " --user-data-dir=""" & profile & """ --window-size=1200,800", 1, False
Else
    sh.Run url, 1, False
End If

' --------------------------------------------------------------------------
Function ServidorNoAr(u)
    On Error Resume Next
    Dim http
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "GET", u, False
    http.Send
    ServidorNoAr = (Err.Number = 0) And (http.Status >= 200) And (http.Status < 500)
    On Error GoTo 0
End Function

Function AcharNavegador()
    Dim c, p
    c = Array( _
        sh.ExpandEnvironmentStrings("%ProgramFiles%") & "\Google\Chrome\Application\chrome.exe", _
        sh.ExpandEnvironmentStrings("%ProgramFiles(x86)%") & "\Google\Chrome\Application\chrome.exe", _
        sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Google\Chrome\Application\chrome.exe", _
        sh.ExpandEnvironmentStrings("%ProgramFiles(x86)%") & "\Microsoft\Edge\Application\msedge.exe", _
        sh.ExpandEnvironmentStrings("%ProgramFiles%") & "\Microsoft\Edge\Application\msedge.exe")
    AcharNavegador = ""
    For Each p In c
        If fso.FileExists(p) Then
            AcharNavegador = p
            Exit Function
        End If
    Next
End Function
