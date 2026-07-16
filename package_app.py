import os
import subprocess
import sys
import shutil

def run_command(command: str, cwd: str = None) -> bool:
    print(f"[*] Running: {command} in {cwd or '.'}")
    res = subprocess.run(command, shell=True, cwd=cwd)
    return res.returncode == 0

def check_dependencies():
    print("[*] Checking packaging dependencies...")
    try:
        import pyinstaller
    except ImportError:
        print("[*] PyInstaller not found. Installing now...")
        run_command(f"{sys.executable} -m pip install pyinstaller")

def build_frontend():
    print("[*] Building React frontend production assets...")
    frontend_dir = os.path.abspath("frontend")
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("[*] Installing frontend dependencies...")
        run_command("npm install", cwd=frontend_dir)
    success = run_command("npm run build", cwd=frontend_dir)
    if not success:
        print("[ERROR] Frontend build failed!")
        sys.exit(1)

def package_backend():
    print("[*] Compiling python backend using PyInstaller...")
    sep = ";" if sys.platform.startswith("win") else ":"
    
    hidden_imports = [
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets.websockets_impl",
        "uvicorn.protocols.websockets.wsproto_impl",
        "uvicorn.lifespan.on",
        "aiosqlite",
        "sqlalchemy.dialects.sqlite.aiosqlite",
        "passlib.handlers.bcrypt",
        "scipy",
        "scipy.special",
        "scipy.linalg",
        "sklearn",
        "sklearn.ensemble",
        "sklearn.model_selection",
        "sklearn.tree",
        "sklearn.utils",
        "pandas",
        "numpy",
        "networkx",
        "matplotlib",
        "matplotlib.pyplot",
        "plotly",
        "plotly.graph_objects",
        "PIL",
        "app.main",
        "app.routers.plant",
        "app.routers.plc",
        "app.routers.communication",
        "app.routers.security",
        "app.routers.risk",
        "app.routers.recovery",
        "app.routers.audit",
        "app.routers.health",
        "app.routers.attack",
        "app.routers.ai",
        "app.routers.trust",
        "app.services.cloud_agent_bridge"
    ]
    
    hidden_import_args = " ".join([f"--hidden-import={imp}" for imp in hidden_imports])
    
    # Paths to bundle
    threat_model_src = os.path.abspath("backend/app/models/threat_model.pkl")
    frontend_dist_src = os.path.abspath("frontend/dist")
    
    # If the threat model doesn't exist, run the python script once to generate it
    if not os.path.exists(threat_model_src):
        print("[*] Generating baseline threat model...")
        sys.path.append(os.path.abspath("backend"))
        from app.models.ml_models import load_threat_model
        load_threat_model()
        
    excludes = [
        "PyQt5", "sphinx", "bokeh", "h5py", "lz4", "distributed", 
        "panel", "skimage", "docutils", "jedi", "IPython", "ipykernel", 
        "notebook", "nbconvert", "tornado", "astropy", 
        "astropy_iers_data", "zope", "pyarrow"
    ]
    exclude_args = " ".join([f"--exclude-module={exc}" for exc in excludes])

    cmd = (
        f"pyinstaller --clean -y --onefile --noconsole --name=OmegaAI "
        f"--icon=omega_logo.ico "
        f"--paths=backend "
        f"--add-data=\"{threat_model_src}{sep}app/models\" "
        f"--add-data=\"{frontend_dist_src}{sep}frontend/dist\" "
        f"{hidden_import_args} "
        f"{exclude_args} "
        f"backend/run.py"
    )
    
    success = run_command(cmd)
    if not success:
        print("[ERROR] Packaging backend executable failed!")
        sys.exit(1)
    print(f"[+] standalone background executable built inside dist/OmegaAI/")

def copy_service_installers():
    print("[*] Copying service installer helpers to dist...")
    # Copy installer and uninstaller helpers to the dist folder
    dist_dir = os.path.abspath("dist/OmegaAI")
    if os.path.exists(dist_dir):
        shutil.copy("install_service.py", dist_dir)
        shutil.copy("uninstall_service.py", dist_dir)
        shutil.copy("install.bat", dist_dir)
        shutil.copy("uninstall.bat", dist_dir)
        print("[+] Copied install_service.py, uninstall_service.py, install.bat, and uninstall.bat helpers into package distribution folder.")

def main():
    check_dependencies()
    # build_frontend()
    package_backend()
    copy_service_installers()
    print("=" * 60)
    print("              OMEGA APP PACKAGING SUCCESSFUL!")
    print("  You can now install the application into startup using:")
    print("  cd dist/OmegaAI")
    print("  python install_service.py --install")
    print("=" * 60)

if __name__ == "__main__":
    main()
