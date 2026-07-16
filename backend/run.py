import sys
import os
import io
import shutil
import subprocess
import asyncio

# Prevent uvicorn/logging crashes in --noconsole (windowed) mode where sys.stdout/sys.stderr are None
class DummyStream(io.IOBase):
    def write(self, s):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False

if sys.stdout is None:
    sys.stdout = DummyStream()
if sys.stderr is None:
    sys.stderr = DummyStream()

# Add parent directory of app to path to ensure all imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Auto-installer for Windows
def check_and_run_installer():
    # Only run installer when packaged by PyInstaller (frozen)
    if getattr(sys, 'frozen', False):
        import platform
        if platform.system() == "Windows":
            appdata_dir = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
            install_dir = os.path.join(appdata_dir, "OmegaAI")
            installed_exe = os.path.join(install_dir, "OmegaAI.exe")
            exe_path_norm = os.path.abspath(sys.executable).lower()
            inst_path_norm = os.path.abspath(installed_exe).lower()
            
            # Check if running from installed path (case insensitive comparison)
            if exe_path_norm != inst_path_norm:
                try:
                    import ctypes
                    # MB_YESNO = 4, MB_ICONINFORMATION = 64
                    res = ctypes.windll.user32.MessageBoxW(
                        0,
                        "Do you want to install OmegaAI on this laptop?\n\nThis will configure it to run in the background 24/7 and auto-start on boot.",
                        "OmegaAI Installer",
                        4 | 64
                    )
                    
                    if res == 6:  # IDYES
                        os.makedirs(install_dir, exist_ok=True)
                        
                        # Copy the executable
                        shutil.copy2(sys.executable, installed_exe)
                        
                        # Register startup key
                        import winreg
                        key = winreg.HKEY_CURRENT_USER
                        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                        reg_key = winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE)
                        winreg.SetValueEx(reg_key, "OmegaAI", 0, winreg.REG_SZ, f'"{installed_exe}"')
                        winreg.CloseKey(reg_key)
                        
                        # Add firewall rule automatically during installation
                        try:
                            subprocess.run(
                                'netsh advfirewall firewall add rule name="OmegaAI Server" dir=in action=allow protocol=TCP localport=8000', 
                                shell=True, 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL
                            )
                        except Exception:
                            pass

                        # Create uninstaller batch file
                        uninstall_bat = os.path.join(install_dir, "Uninstall_OmegaAI.bat")
                        with open(uninstall_bat, "w") as f:
                            f.write(f"""@echo off
title OmegaAI Uninstaller
echo ============================================================
echo          UNINSTALLING OMEGA AI BACKGROUND DAEMON
echo ============================================================
echo.
taskkill /IM OmegaAI.exe /F >nul 2>&1
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "OmegaAI" /f >nul 2>&1
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\OmegaAI" /f >nul 2>&1
netsh advfirewall firewall delete rule name="OmegaAI Server" >nul 2>&1
echo [+] OmegaAI startup registry value removed.
echo [+] OmegaAI Add/Remove registry key removed.
echo [+] OmegaAI firewall rule removed.
echo [+] OmegaAI process terminated.
echo.
echo Uninstallation complete! You can now close this window and delete the folder.
pause
""")
                        
                        # Register in Add/Remove Programs (Apps & Features)
                        uninstall_key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaAI"
                        try:
                            un_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, uninstall_key_path)
                            winreg.SetValueEx(un_key, "DisplayName", 0, winreg.REG_SZ, "Omega Cyber Resilience Platform")
                            winreg.SetValueEx(un_key, "UninstallString", 0, winreg.REG_SZ, f'cmd.exe /c "{uninstall_bat}"')
                            winreg.SetValueEx(un_key, "DisplayIcon", 0, winreg.REG_SZ, installed_exe)
                            winreg.SetValueEx(un_key, "Publisher", 0, winreg.REG_SZ, "Omega Security")
                            winreg.SetValueEx(un_key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
                            winreg.SetValueEx(un_key, "NoModify", 0, winreg.REG_DWORD, 1)
                            winreg.SetValueEx(un_key, "NoRepair", 0, winreg.REG_DWORD, 1)
                            winreg.SetValueEx(un_key, "EstimatedSize", 0, winreg.REG_DWORD, 419840)
                            winreg.CloseKey(un_key)
                            print("[+] SUCCESS: Registered in Windows Add/Remove Programs.")
                        except Exception as reg_err:
                            print(f"[ERROR] Add/Remove registry failed: {reg_err}")
                        
                        # Spawn installed process in background
                        subprocess.Popen(
                            [installed_exe],
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                        )
                        
                        # Show success popup
                        ctypes.windll.user32.MessageBoxW(
                            0,
                            "OmegaAI has been successfully installed and is now running in the background 24/7.\n\nAn uninstaller is created at:\n" + uninstall_bat,
                            "OmegaAI Installer",
                            64
                        )
                        sys.exit(0)
                except Exception as e:
                    print(f"[ERROR] Installer failed: {e}")

# Run installer check
check_and_run_installer()

import uvicorn
from app.main import app
from app.services.agent_client import start_agent

async def start_all():
    # 0. Configure Windows Defender Firewall rule automatically on startup
    import platform
    if platform.system() == "Windows":
        try:
            import subprocess
            subprocess.run(
                'netsh advfirewall firewall add rule name="OmegaAI Server" dir=in action=allow protocol=TCP localport=8000', 
                shell=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            print("[+] Windows Defender Firewall rule verified/added for port 8000.")
        except Exception as fw_err:
            print(f"[WARNING] Automatic firewall rule configuration failed: {fw_err}")

    # 1. Initialize database schema before starting any background loops
    from app.database import engine, Base
    print("[*] Initializing database schema...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[+] Database schema initialized successfully.")
    except Exception as db_err:
        print(f"[WARNING] Database pre-initialization failed: {db_err}. Will retry in server lifespan.")

    # 1.5. Launch localtunnel background bridge
    try:
        import subprocess
        import platform
        creationflags = 0
        if platform.system() == "Windows":
            creationflags = 0x08000000  # CREATE_NO_WINDOW
        
        # Spawn localtunnel background process
        subprocess.Popen(
            "npx -y localtunnel --port 8000 --subdomain omega-cyber-immunity",
            shell=True,
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("[+] Started localtunnel background bridge at https://omega-cyber-immunity.loca.lt")
    except Exception as lt_err:
        print(f"[WARNING] Failed to spawn localtunnel automatically: {lt_err}")

    # 2. Programmatic uvicorn server configuration
    # Listening on 0.0.0.0 enables Android connection on the local network
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    
    # Run both the FastAPI server and the agent client concurrently
    await asyncio.gather(
        server.serve(),
        start_agent()
    )

if __name__ == "__main__":
    print("[*] Starting Omega Cyber Resilience Platform (Server + Agent)...")
    try:
        asyncio.run(start_all())
    except KeyboardInterrupt:
        print("\n[*] Platform stopped by user.")

