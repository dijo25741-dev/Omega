import os
import sys
import argparse
import platform

def install_windows_startup(exe_path: str):
    import winreg
    print(f"[*] Registering startup registry key for Windows...")
    key = winreg.HKEY_CURRENT_USER
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        reg_key = winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(reg_key, "OmegaAI", 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(reg_key)
        print(f"[+] SUCCESS: Registered OmegaAI auto-startup in User Registry.")
        print(f"    Path: {exe_path}")
        
        # Configure Windows Defender Firewall rule automatically
        print("[*] Configuring Windows Defender Firewall rule for port 8000...")
        import subprocess
        subprocess.run(
            'netsh advfirewall firewall add rule name="OmegaAI Server" dir=in action=allow protocol=TCP localport=8000', 
            shell=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        print("[+] SUCCESS: Firewall rule configured for incoming connections.")
        
        # Now register in Add/Remove Programs (Apps & Features)
        dist_dir = os.path.dirname(os.path.abspath(__file__))
        uninstall_bat = os.path.join(dist_dir, "uninstall.bat")
        
        # Fallback if uninstall.bat is next to the executable
        if not os.path.exists(uninstall_bat):
            uninstall_bat = os.path.join(os.path.dirname(exe_path), "uninstall.bat")
            
        if os.path.exists(uninstall_bat):
            uninstall_key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaAI"
            un_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, uninstall_key_path)
            winreg.SetValueEx(un_key, "DisplayName", 0, winreg.REG_SZ, "Omega Cyber Resilience Platform")
            winreg.SetValueEx(un_key, "UninstallString", 0, winreg.REG_SZ, f'cmd.exe /c "{uninstall_bat}"')
            winreg.SetValueEx(un_key, "DisplayIcon", 0, winreg.REG_SZ, exe_path)
            winreg.SetValueEx(un_key, "Publisher", 0, winreg.REG_SZ, "Omega Security")
            winreg.SetValueEx(un_key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(un_key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(un_key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(un_key, "EstimatedSize", 0, winreg.REG_DWORD, 419840)
            winreg.CloseKey(un_key)
            print("[+] SUCCESS: Registered in Windows Add/Remove Programs.")
        else:
            print("[WARNING] Could not locate uninstall.bat helper. Skipping Add/Remove registration.")
            
    except Exception as e:
        print(f"[ERROR] Failed to write registry key: {e}")

def uninstall_windows_startup():
    import winreg
    print(f"[*] Removing startup and uninstall registry keys for Windows...")
    try:
        # Remove startup registry key
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            reg_key = winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(reg_key, "OmegaAI")
            winreg.CloseKey(reg_key)
            print("[+] Removed startup registry key.")
        except FileNotFoundError:
            print("[*] Startup registry key not found.")
            
        # Remove uninstall registry key
        uninstall_key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaAI"
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, uninstall_key_path)
            print("[+] Removed Add/Remove Programs registry key.")
        except FileNotFoundError:
            print("[*] Add/Remove Programs registry key not found.")
            
        # Remove firewall rule automatically
        print("[*] Removing Windows Defender Firewall rule...")
        import subprocess
        subprocess.run(
            'netsh advfirewall firewall delete rule name="OmegaAI Server"', 
            shell=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        print("[+] Removed Windows Defender Firewall rule.")
            
    except Exception as e:
        print(f"[ERROR] Failed to delete registry key: {e}")

def install_macos_launchagent(exe_path: str):
    import subprocess
    plist_dir = os.path.expanduser("~/Library/LaunchAgents")
    os.makedirs(plist_dir, exist_ok=True)
    plist_path = os.path.join(plist_dir, "com.omega.shield.plist")
    plist_path = os.path.join(plist_dir, "com.omega.ai.plist")
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.omega.ai</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{os.path.expanduser('~/Library/Logs/omega_shield.log')}</string>
    <key>StandardErrorPath</key>
    <string>{os.path.expanduser('~/Library/Logs/omega_shield_err.log')}</string>
</dict>
</plist>
"""
    try:
        with open(plist_path, "w") as f:
            f.write(plist_content)
        print(f"[+] Written LaunchAgent config to {plist_path}")
        
        # Load the LaunchAgent
        subprocess.run(["launchctl", "unload", plist_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["launchctl", "load", plist_path])
        print(f"[+] SUCCESS: Registered & Started com.omega.ai background LaunchAgent.")
    except Exception as e:
        print(f"[ERROR] Failed to install macOS LaunchAgent: {e}")

def uninstall_macos_launchagent():
    import subprocess
    plist_path = os.path.expanduser("~/Library/LaunchAgents/com.omega.ai.plist")
    if os.path.exists(plist_path):
        subprocess.run(["launchctl", "unload", plist_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            os.remove(plist_path)
            print(f"[+] SUCCESS: Removed macOS LaunchAgent plist configuration.")
        except Exception as e:
            print(f"[ERROR] Failed to delete LaunchAgent: {e}")
    else:
        print("[*] LaunchAgent configuration not found.")

def main():
    parser = argparse.ArgumentParser(description="Omega Background Service Startup Installer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install", action="store_true", help="Register app in boot-time startup sequence")
    group.add_argument("--uninstall", action="store_true", help="Unregister app from boot-time startup sequence")
    args = parser.parse_args()
    
    current_os = platform.system()
    
    if args.install:
        # Determine executable name based on OS
        binary_name = "OmegaAI.exe" if current_os == "Windows" else "OmegaAI"
        
        # Look for executable in current folder or standard PyInstaller dist directories
        paths_to_check = [
            os.path.abspath(binary_name),
            os.path.abspath(os.path.join(os.path.dirname(__file__), binary_name)),
            os.path.abspath(os.path.join(os.path.dirname(__file__), f"dist/OmegaAI/{binary_name}"))
        ]
        
        exe_path = None
        for p in paths_to_check:
            if os.path.exists(p) and not os.path.isdir(p):
                exe_path = p
                break
                
        if not exe_path:
            print(f"[ERROR] Could not locate compiled executable file ({binary_name}).")
            print(f"Please run the packaging script first: 'python package_app.py'")
            sys.exit(1)
            
        print(f"[*] Found executable path: {exe_path}")
        
        if current_os == "Windows":
            install_windows_startup(exe_path)
        elif current_os == "Darwin":  # macOS
            install_macos_launchagent(exe_path)
        else:
            print(f"[ERROR] Auto-startup install not supported on OS: {current_os}")
            sys.exit(1)
            
    elif args.uninstall:
        if current_os == "Windows":
            uninstall_windows_startup()
        elif current_os == "Darwin":
            uninstall_macos_launchagent()
        else:
            print(f"[ERROR] Auto-startup uninstall not supported on OS: {current_os}")
            sys.exit(1)

if __name__ == "__main__":
    main()
