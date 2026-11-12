Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\SSBD-202506-02\Documents\GitHub\EMS-Expense-App"
WshShell.Run """C:\Users\SSBD-202506-02\AppData\Local\Python\bin\python.exe"" app.py", 0, False
