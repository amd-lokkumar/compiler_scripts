#!/usr/bin/python3

import os
import subprocess
import sys

def usage():
    print("Usage: python install_intel.py [version]")
    print("Example: python install_intel.py 2025.0")
    sys.exit(1)

def check_command(command):
    return subprocess.call(f"command -v {command}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def install_packages():
    print("Installing required packages...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "build-essential", "wget", "-y"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        sys.exit(1)

def install_environment_modules():
    if not check_command("module"):
        print("Installing environment-modules...")
        try:
            subprocess.run(["sudo", "apt", "install", "--no-install-recommends", "environment-modules", "-y"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing environment-modules: {e}")
            sys.exit(1)

def download_intel_toolkit(version):
    print(f"Downloading Intel oneAPI Base and HPC Toolkits version {version}...")
    
    # Updated download links for the toolkits
    base_toolkit_url = "https://registrationcenter-download.intel.com/akdlm/IRC_NAS/dfc4a434-838c-4450-a6fe-2fa903b75aa7/intel-oneapi-base-toolkit-2025.0.1.46_offline.sh"
    hpc_toolkit_url = "https://registrationcenter-download.intel.com/akdlm/IRC_NAS/b7f71cf2-8157-4393-abae-8cea815509f7/intel-oneapi-hpc-toolkit-2025.0.1.47_offline.sh"

    try:
        subprocess.run(["wget", base_toolkit_url], check=True)
        subprocess.run(["wget", hpc_toolkit_url], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading toolkits: {e}")
        sys.exit(1)

def extract_and_install(install_dir):
    print("Installing Intel oneAPI Toolkits silently...")
    
    try:
        os.makedirs(install_dir, exist_ok=True)

        # Silent installation commands for both toolkits
        subprocess.run([
            "sh", 
            "intel-oneapi-base-toolkit-2025.0.1.46_offline.sh", 
            "-a", 
            "--silent", 
            "--eula=accept", 
            f"--install-dir={install_dir}"
        ], check=True)
        
        subprocess.run([
            "sh", 
            "intel-oneapi-hpc-toolkit-2025.0.1.47_offline.sh", 
            "-a", 
            "--silent", 
            "--eula=accept",
            f"--install-dir={install_dir}"
        ], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error during installation process: {e}")
        sys.exit(1)

def create_module_file(version, install_dir):
    modulefile_dir = os.path.expanduser(f"~/compiler_modulefiles/intel")
    os.makedirs(modulefile_dir, exist_ok=True)
    
    modulefile_path = os.path.join(modulefile_dir, f"intel-{version}")
    
    try:
        with open(modulefile_path, 'w') as f:
            f.write(f"""#%Module1.0

proc ModulesHelp {{ }} {{
    global version modroot
    puts stderr "Intel oneAPI Base and HPC Toolkits version {version} - sets the environment for intel-{version}"
}}

module-whatis "Sets the environment for Intel oneAPI Base and HPC Toolkits version {version}"

set topdir {install_dir}
set version {version}

setenv CC ${{topdir}}/compiler/bin/icx
setenv CXX ${{topdir}}/compiler/bin/icpx
prepend-path PATH ${{topdir}}/compiler/bin
prepend-path LD_LIBRARY_PATH ${{topdir}}/compiler/lib
""")
    except IOError as e:
        print(f"Error creating module file: {e}")
        sys.exit(1)

def update_bashrc():
    bashrc_path = os.path.expanduser("~/.bashrc")
    
    try:
        with open(bashrc_path, 'r') as bashrc:
            content = bashrc.read()
        
        if 'export MODULEPATH' not in content:
            with open(bashrc_path, 'a') as bashrc:
                bashrc.write('export MODULEPATH=${MODULEPATH}:$HOME/compiler_modulefiles\n')
                print("Added MODULEPATH to .bashrc.")
                print("Please run 'source ~/.bashrc' or restart your terminal to update your environment.")
                
                return True
        else:
            print("MODULEPATH already exists in .bashrc.")
            return False
            
    except IOError as e:
        print(f"Error updating .bashrc: {e}")
        sys.exit(1)

def main():
   if len(sys.argv) < 2:
       usage()
   
   version = sys.argv[1]
   
   install_dir = os.path.expanduser(f"~/compiler_installation/intel-{version}")

   if os.path.isdir(install_dir):
       print(f"Intel oneAPI Toolkits version {version} is already installed in {install_dir}.")
       create_module_file(version, install_dir)
       update_bashrc()
       return

   os.makedirs(install_dir, exist_ok=True)
   install_packages()
   install_environment_modules()
#    download_intel_toolkit(version)
   extract_and_install(install_dir)
   create_module_file(version, install_dir)
   update_bashrc()

   print(f"Intel oneAPI Toolkits version {version} has been installed successfully in {install_dir}.")
   print(f"Module file created at ~/compiler_modulefiles/intel/intel-{version}.")

if __name__ == "__main__":
   main()
