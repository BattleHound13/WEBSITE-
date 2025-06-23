@echo off
:: Check for administrative privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Please run this script as an administrator.
    pause
    exit
)

:: List all WiFi profiles into a temporary file
netsh wlan show profiles > temp_profiles.txt

:: Process each line in the file to extract WiFi profile names
for /f "tokens=1,* delims=:" %%A in ('findstr /c:"All User Profile" temp_profiles.txt') do (
    set "profile=%%B"
    call :show_password
)

:: Clean up temporary file
del temp_profiles.txt
pause
exit

:show_password
setlocal enabledelayedexpansion
:: Remove leading spaces from the profile name
set "profile=!profile:~1!"
:: Display the WiFi profile and attempt to retrieve the password
echo -----------------------------------
echo WiFi Network: !profile!
netsh wlan show profile name="!profile!" key=clear | findstr /c:"Key Content" || echo Password not found or no access.
echo -----------------------------------
endlocal
goto :eof
