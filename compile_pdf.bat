@echo off
REM Batch script to compile LaTeX paper to PDF
echo Compiling TrackAI Research Paper to PDF...
echo.

REM Check if pdflatex is available
where pdflatex >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pdflatex not found in PATH
    echo.
    echo Please install LaTeX distribution:
    echo 1. MiKTeX: https://miktex.org/download
    echo 2. Or use online: https://www.overleaf.com
    echo.
    echo To install MiKTeX via winget:
    echo   winget install --id MiKTeX.MiKTeX
    echo.
    pause
    exit /b 1
)

cd papers
echo Running pdflatex (first pass)...
pdflatex -interaction=nonstopmode TrackAI-IEEE.tex
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: First compilation failed
    pause
    exit /b 1
)

echo Running pdflatex (second pass for references)...
pdflatex -interaction=nonstopmode TrackAI-IEEE.tex

if exist TrackAI-IEEE.pdf (
    echo.
    echo SUCCESS! PDF created: papers\TrackAI-IEEE.pdf
) else (
    echo ERROR: PDF was not created
)

cd ..
pause

