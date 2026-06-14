@echo off

title CupNet - Build

echo.

echo  ========================================

echo   CupNet - Generation de l'executable

echo  ========================================

echo.

echo  ASTUCE : vous n'avez PAS besoin de compiler !

echo  Utilisez LANCER-CupNet.bat directement.

echo.



cd /d "%~dp0backend"



if not exist ".venv" (

    echo Creation de l'environnement virtuel...

    python -m venv .venv

)



call .venv\Scripts\activate.bat

pip install -r requirements.txt -q



echo.

echo  Fermez CupNet s'il est ouvert, puis compilation...

echo.



taskkill /IM CupNet.exe /F >nul 2>&1

timeout /t 2 /nobreak >nul



pyinstaller CupNet.spec --noconfirm



if exist "dist\CupNet.exe" (

    echo.

    echo  ========================================

    echo   SUCCES !

    echo   Executable : backend\dist\CupNet.exe

    echo  ========================================

    echo.

) else (

    echo.

    echo  Compilation echouee — utilisez LANCER-CupNet.bat

    echo  Utilisez LANCER-CupNet.bat directement.

    echo.

)



pause

