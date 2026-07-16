import os
import sys
import platform
import subprocess

def main():
    print("=" * 60)
    print("              OMEGA SHIELD UNINSTALLER")
    print("=" * 60)
    
    current_os = platform.system()
    
    # 1. Unregister auto-startup registry key / launchagent
    if current_os == "Windows":
        try:
            import winreg
            print("[*] Removing Windows registry keys...")
            
            # Remove Run startup key
            try:
                key = winreg.HKEY_CURRENT_USER
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                reg_key = winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(reg_key, "OmegaAI")
                winreg.CloseKey(reg_key)
                print("[+] Startup registry key removed.")
            except FileNotFoundError:
                print("[*] Startup registry key already removed or not found.")
                
            # Remove Uninstall key
            try:
                uninstall_key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\OmegaAI"
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, uninstall_key_path)
                print("[+] Add/Remove Programs registry key removed.")
            except FileNotFoundError:
                print("[*] Add/Remove Programs registry key already removed or not found.")
                
        except Exception as e:
            print(f"[ERROR] Failed to delete registry keys: {e}")
            
    elif current_os == "Darwin":  # macOS
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.omega.ai.plist")
        if os.path.exists(plist_path):
            subprocess.run(["launchctl", "unload", plist_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                os.remove(plist_path)
                print("[+] macOS LaunchAgent plist configuration removed.")
            except Exception as e:
                print(f"[ERROR] Failed to delete LaunchAgent: {e}")
        else:
            print("[*] macOS LaunchAgent configuration not found.")
            
    # 2. Terminate running background process
    if current_os == "Windows":
        print("[*] Terminating running OmegaAI process...")
        subprocess.run("taskkill /IM OmegaAI.exe /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] Process terminated.")
    elif current_os == "Darwin":
        print("[*] Terminating running OmegaAI process...")
        subprocess.run("pkill -f OmegaAI", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] Process terminated.")
        
    print("[+] Uninstallation complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
