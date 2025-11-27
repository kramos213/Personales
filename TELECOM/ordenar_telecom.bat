@echo off
echo ================================
echo  ORDENANDO PROYECTO TELECOM
echo ================================
echo.

set ROOT=%cd%

echo Creando estructura de carpetas...
mkdir src 2>nul
mkdir src\scanners 2>nul
mkdir src\monitoreo 2>nul
mkdir src\switches 2>nul
mkdir src\usuarios 2>nul
mkdir src\pruebas 2>nul
mkdir config 2>nul
mkdir outputs 2>nul
mkdir outputs\logs 2>nul
mkdir outputs\csv 2>nul
mkdir outputs\reportes 2>nul
mkdir docs 2>nul

echo.
echo Moviendo archivos a sus nuevas rutas...
echo.

:: SCANNERS
move /Y "%ROOT%\network_scanner.py" "%ROOT%\src\scanners\" 
move /Y "%ROOT%\latencia_checker.py" "%ROOT%\src\scanners\" 
move /Y "%ROOT%\Puerto activo.py" "%ROOT%\src\scanners\" 

:: MONITOREO
move /Y "%ROOT%\Monitor de Red.py" "%ROOT%\src\monitoreo\" 
move /Y "%ROOT%\Monitor de Red 2.0.py" "%ROOT%\src\monitoreo\" 
move /Y "%ROOT%\dasboarch de monitoreo.py" "%ROOT%\src\monitoreo\" 

:: SWITCHES
move /Y "%ROOT%\backup_switches.py" "%ROOT%\src\switches\" 
move /Y "%ROOT%\Update_switch.py" "%ROOT%\src\switches\" 
move /Y "%ROOT%\Arista Respaldo.py" "%ROOT%\src\switches\" 
move /Y "%ROOT%\Log Switches.py" "%ROOT%\src\switches\" 
move /Y "%ROOT%\Reporte estatus de Interfaz.py" "%ROOT%\src\switches\" 
move /Y "%ROOT%\Script Log de Sw.py" "%ROOT%\src\switches\" 
move /Y "%ROOT%\VLAN_puertos.py" "%ROOT%\src\switches\" 
move /Y "%ROOT%\Report POE.py" "%ROOT%\src\switches\" 

:: USUARIOS
move /Y "%ROOT%\Usuario.py" "%ROOT%\src\usuarios\" 
move /Y "%ROOT%\Script config-usuario.py" "%ROOT%\src\usuarios\" 

:: PRUEBAS
move /Y "%ROOT%\Pruebas.py" "%ROOT%\src\pruebas\" 

echo.
echo Creando archivos base de configuracion...
echo "# Lista de redes a escanear" > config\redes.txt
echo "# Lista de switches" > config\switches.txt
echo "# Lista de usuarios" > config\usuarios.txt
echo "{}" > config\parametros.json
echo "22" > config\puertos.txt
echo "80" >> config\puertos.txt
echo "443" >> config\puertos.txt

echo.
echo Creando archivo de documentación...
echo "# Proyecto TELECOM - Documentación" > docs\notas.md

echo.
echo Todo organizado correctamente.
echo Estructura final creada en:
echo %ROOT%

pause
