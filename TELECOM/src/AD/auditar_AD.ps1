<#
.SYNOPSIS
    Auditoría completa de Active Directory.
.DESCRIPTION
    Ejecuta dcdiag, repadmin, FSMO, DNS, GPOs, usuarios/equipos inactivos,
    políticas, roles administrativos, trusts, logs críticos y genera HTML resumen.
.NOTES
    Ejecutar como Administrador. Requiere módulo ActiveDirectory (RSAT).
#>

# ------------------------------------
# CONFIGURACIÓN DE CARPETA DE SALIDA
# ------------------------------------

# 👉 CAMBIA ESTA RUTA POR LA QUE QUIERAS
$OutputRoot = "C:\AD-AUDIT"

# Carpeta con timestamp
$OutputRoot = Join-Path $OutputRoot ("AUDIT-" + (Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'))
New-Item -Path $OutputRoot -ItemType Directory -Force | Out-Null

$DaysInactiveUsers = 90
$DaysInactiveComputers = 60

# ------------------------------------
# FUNCIÓN DE EJECUCIÓN SEGURA
# ------------------------------------
function Run-External {
    param(
        [string]$Cmd,
        [string]$OutFile = $null
    )
    try {
        Write-Host "-> Ejecutando: $Cmd" -ForegroundColor Cyan
        $out = & cmd.exe /c $Cmd 2>&1
        if ($OutFile) { $out | Out-File -FilePath $OutFile -Encoding utf8 }
        return $out
    } catch {
        $_ | Out-File -FilePath (Join-Path $OutputRoot "errors.txt") -Append
        return $_.Exception.Message
    }
}

# ------------------------------------
# PRERREQUISITOS
# ------------------------------------
Write-Host "Iniciando auditoría AD..." -ForegroundColor Green

# ================================
# Validar permisos de administrador
# ================================
if (-not (
    [Security.Principal.WindowsPrincipal] (
        [Security.Principal.WindowsIdentity]::GetCurrent()
    )
).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {

    Write-Host "❌ Debes ejecutar PowerShell como Administrador." -ForegroundColor Red
    exit
}


# Módulo AD
try {
    Import-Module ActiveDirectory -ErrorAction Stop
} catch {
    Write-Warning "No se pudo cargar el módulo ActiveDirectory. Instala RSAT."
}

# ------------------------------------
# 1. DCDIAG
# ------------------------------------
Run-External "dcdiag /v" -OutFile (Join-Path $OutputRoot "dcdiag_v.txt")

# ------------------------------------
# 2. REPADMIN
# ------------------------------------
Run-External "repadmin /replsummary" -OutFile (Join-Path $OutputRoot "repadmin_replsummary.txt")
Run-External "repadmin /showrepl * /csv" -OutFile (Join-Path $OutputRoot "repadmin_showrepl.txt")

# ------------------------------------
# 3. FSMO
# ------------------------------------
Run-External "netdom query fsmo" -OutFile (Join-Path $OutputRoot "fsmo_roles.txt")

# ------------------------------------
# 4. PRUEBAS DNS
# ------------------------------------
Run-External "dcdiag /test:dns /v" -OutFile (Join-Path $OutputRoot "dns_tests.txt")

# ------------------------------------
# 5. TIME SYNC
# ------------------------------------
Run-External "w32tm /query /status" -OutFile (Join-Path $OutputRoot "w32tm_status.txt")
Run-External "w32tm /query /configuration" -OutFile (Join-Path $OutputRoot "w32tm_config.txt")

# ------------------------------------
# 6. SERVICIOS DE LOS DCs
# ------------------------------------
$DCs = Get-ADDomainController -Filter * 

foreach ($dc in $DCs) {
    $dcName = $dc.HostName
    try {
        Get-Service -ComputerName $dcName |
            Where-Object { $_.Name -in @('kdc','dns','netlogon','ntfrs','adws','w32time') } |
            Select-Object Name,DisplayName,Status |
            Export-Csv -Path (Join-Path $OutputRoot "services_$dcName.csv") -NoTypeInformation
    } catch {
        Write-Warning "No se pudo consultar servicios en $dcName"
    }
}

# ------------------------------------
# 7. USUARIOS
# ------------------------------------
Search-ADAccount -AccountInactive -UsersOnly -DateTime (Get-Date).AddDays(-$DaysInactiveUsers) |
    Select Name,SamAccountName,LastLogonDate |
    Export-Csv (Join-Path $OutputRoot "usuarios_inactivos.csv") -NoTypeInformation

Get-ADUser -Filter {PasswordNeverExpires -eq $true} -Properties PasswordNeverExpires |
    Select Name,SamAccountName,PasswordNeverExpires |
    Export-Csv (Join-Path $OutputRoot "usuarios_pwd_never.csv") -NoTypeInformation

Search-ADAccount -LockedOut |
    Select Name,SamAccountName |
    Export-Csv (Join-Path $OutputRoot "usuarios_bloqueados.csv") -NoTypeInformation

# ------------------------------------
# 8. COMPUTERS
# ------------------------------------
Search-ADAccount -AccountInactive -ComputersOnly -DateTime (Get-Date).AddDays(-$DaysInactiveComputers) |
    Select Name,SamAccountName,LastLogonDate |
    Export-Csv (Join-Path $OutputRoot "computers_inactivos.csv") -NoTypeInformation

# ------------------------------------
# 9. GPOs
# ------------------------------------
Get-GPO -All |
    Select DisplayName,Id,CreationTime,ModificationTime |
    Export-Csv (Join-Path $OutputRoot "gpo_list.csv") -NoTypeInformation

gpresult /h (Join-Path $OutputRoot "gpresult_local.html")

# ------------------------------------
# 10. PASSWORD POLICY
# ------------------------------------
Get-ADDefaultDomainPasswordPolicy |
    Select MinPasswordLength,MaxPasswordAge,LockoutDuration,LockoutThreshold |
    Export-Csv (Join-Path $OutputRoot "password_policy.csv") -NoTypeInformation

# ------------------------------------
# 11. GRUPOS ADMIN
# ------------------------------------
$adminGroups = @("Domain Admins","Enterprise Admins","Schema Admins","Administrators")

foreach ($grp in $adminGroups) {
    try {
        Get-ADGroupMember $grp -Recursive |
            Select Name,SamAccountName,objectClass |
            Export-Csv (Join-Path $OutputRoot "$($grp -replace ' ','_').csv") -NoTypeInformation
    } catch {
        Write-Warning "No se pudo leer el grupo $grp"
    }
}

# ------------------------------------
# 12. TRUSTS
# ------------------------------------
try {
    Get-ADTrust -Filter * |
        Select Source,Target,Direction,TrustType |
        Export-Csv (Join-Path $OutputRoot "trusts.csv") -NoTypeInformation
} catch {}

# ------------------------------------
# 13. EVENT LOGS (7 días)
# ------------------------------------
$since = (Get-Date).AddDays(-7)

Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$since} |
    Select TimeCreated,Id,LevelDisplayName,Message |
    Export-Csv (Join-Path $OutputRoot "eventos_system.csv") -NoTypeInformation

# ------------------------------------
# 14. RESUMEN HTML
# ------------------------------------
$html = @"
<html><body>
<h1>Resumen de Auditoría AD</h1>
<p>Generado: $(Get-Date)</p>
<p>Carpeta: $OutputRoot</p>
<ul>
<li>DCDIAG, DNS, Repadmin</li>
<li>Usuarios inactivos, equipos inactivos</li>
<li>GPOs, FSMO, Trusts</li>
<li>Logs críticos, servicios DC</li>
</ul>
</body></html>
"@

$html | Out-File (Join-Path $OutputRoot "AD_Audit_Summary.html") -Encoding utf8

Write-Host "`nAuditoría completada. Archivos guardados en: $OutputRoot" -ForegroundColor Green
# ------------------------------------