import os
from PIL import Image

src_img_path = r"C:\Users\Dijo Giftson\.gemini\antigravity\brain\d9b45644-5112-46f0-a7f4-dd4e41bf55a5\media__1784120011679.jpg"
workspace_dir = r"c:\Users\Dijo Giftson\Desktop\Omega"

def main():
    if not os.path.exists(src_img_path):
        print(f"[ERROR] Source image not found at: {src_img_path}")
        return

    # Load source image
    img = Image.open(src_img_path)

    # 1. Create .ico for Windows Laptop App
    ico_dest = os.path.join(workspace_dir, "omega_logo.ico")
    # Windows ico standard sizes
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_dest, format="ICO", sizes=sizes)
    print(f"[+] Saved Windows Icon to: {ico_dest}")

    # 2. Save Android launcher mipmap icons
    res_dir = os.path.join(workspace_dir, "mobile app", "mobile_guardian", "android", "app", "src", "main", "res")
    
    mipmap_configs = {
        "mipmap-mdpi": (48, 48),
        "mipmap-hdpi": (72, 72),
        "mipmap-xhdpi": (96, 96),
        "mipmap-xxhdpi": (144, 144),
        "mipmap-xxxhdpi": (192, 192)
    }

    for mipmap_folder, size in mipmap_configs.items():
        dest_folder = os.path.join(res_dir, mipmap_folder)
        os.makedirs(dest_folder, exist_ok=True)
        dest_file = os.path.join(dest_folder, "ic_launcher.png")
        
        # Resize and save
        resized_img = img.resize(size, Image.Resampling.LANCZOS)
        resized_img.save(dest_file, "PNG")
        print(f"[+] Updated launcher icon: {dest_file} ({size[0]}x{size[1]})")

    print("[SUCCESS] All icons updated!")

if __name__ == "__main__":
    main()
