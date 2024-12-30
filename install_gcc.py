#!/usr/bin/python3

import os
import subprocess
import sys
import requests
import tarfile
import sys

def usage():
    print("Usage: python install_gcc.py [version]")
    print("Example: python install_gcc.py 14.2.0")
    sys.exit(1)

def check_command(command):
    return subprocess.call(f"command -v {command}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def install_packages():
    print("Installing required packages...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "build-essential", "libmpfr-dev", "libgmp3-dev", "libmpc-dev", "-y"], check=True)
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

def download_gcc(version):
    tarball = f"gcc-{version}.tar.gz"
    if not os.path.isfile(tarball):
        print(f"Downloading GCC version {version}...")
        url = f"http://ftp.gnu.org/gnu/gcc/gcc-{version}/{tarball}"
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an error for bad responses
            
            total_size = int(response.headers.get('content-length', 0))
            with open(tarball, 'wb') as file:
                downloaded_size = 0
                chunk_size = 1024  # 1 KB chunks
                for data in response.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    downloaded_size += len(data)
                    # Print progress
                    done = int(50 * downloaded_size / total_size)  # Progress bar length
                    sys.stdout.write(f"\r[{'#' * done}{'-' * (50 - done)}] {downloaded_size / (1024 * 1024):.2f} MB / {total_size / (1024 * 1024):.2f} MB")
                    sys.stdout.flush()
            print()  
            
        except Exception as e:
            print(f"Error downloading GCC: {e}")
            sys.exit(1)
    else:
        print(f"GCC tarball '{tarball}' already exists. Skipping download.")

def extract_gcc(version):
    print("Extracting GCC...")
    try:
        with tarfile.open(f"gcc-{version}.tar.gz", "r:gz") as tar:
            tar.extractall()
    except Exception as e:
        print(f"Error extracting GCC: {e}")
        sys.exit(1)

def configure_gcc(version, install_dir):
    print("Configuring GCC...")
    os.chdir(f"gcc-{version}")
    
    try:
        subprocess.run([
            "./configure",
            "-v",
            f"--prefix={install_dir}",
            "--enable-checking=release",
            "--enable-languages=c,c++,fortran",
            "--disable-multilib",
            "--program-transform-name=s/^gcc$/gcc/;s/^g++$/g++/"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Configuration failed: {e}")
        sys.exit(1)

def compile_gcc():
    print("Compiling GCC... This may take some time.")
    try:
        subprocess.run(["make", "-j$(nproc)"], shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)

def install_gcc():
    print("Installing GCC...")
    try:
        subprocess.run(["sudo", "make", "install"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Installation failed: {e}")
        sys.exit(1)

def create_module_file(version, install_dir):
    modulefile_dir = os.path.expanduser(f"~/compiler_modulefiles/gcc")
    os.makedirs(modulefile_dir, exist_ok=True)
    
    modulefile_path = os.path.join(modulefile_dir, f"gcc-{version}")
    
    try:
        with open(modulefile_path, 'w') as f:
            f.write(f"""#%Module1.0

proc ModulesHelp {{ }} {{
    global version modroot
    puts stderr "GCC version {version} - sets the environment for gcc-{version}"
}}

module-whatis "Sets the environment for GCC version {version}"

set topdir {install_dir}
set version {version}

setenv CC ${{topdir}}/bin/gcc
setenv CXX ${{topdir}}/bin/g++
prepend-path PATH ${{topdir}}/bin
prepend-path LD_LIBRARY_PATH ${{topdir}}/lib
""")
    except IOError as e:
        print(f"Error creating module file: {e}")
        sys.exit(1)

def update_bashrc():
    bashrc_path = os.path.expanduser("~/.bashrc")
    
    try:
        # Read existing .bashrc content to check for MODULEPATH
        with open(bashrc_path, 'r') as bashrc:
            content = bashrc.read()
        
        # Append MODULEPATH if it doesn't exist
        if 'export MODULEPATH' not in content:
            with open(bashrc_path, 'a') as bashrc:
                bashrc.write('export MODULEPATH=${MODULEPATH}:$HOME/compiler_modulefiles\n')
                print("Added MODULEPATH to .bashrc.")
                
                # Inform user to source .bashrc
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
   
   # Default to 14.2.0 if no version is provided
   if not version:
       version = "14.2.0"
   
   install_dir = os.path.expanduser(f"~/compiler_installation/gcc-{version}")

   # Check if GCC is already installed
   if os.path.isfile(os.path.join(install_dir, 'bin', 'gcc')):
       print(f"GCC version {version} is already installed in {install_dir}.")
       
       create_module_file(version, install_dir)
       update_bashrc()
       
       return

   # Create installation directory
   os.makedirs(install_dir, exist_ok=True)

   # Install required packages
   install_packages()

   # Install environment modules
   install_environment_modules()

   # Download and extract GCC
   download_gcc(version)
   
   extract_gcc(version)

   # Configure and compile GCC
   configure_gcc(version, install_dir)
   
   compile_gcc()
   
   # Install GCC
   install_gcc()

   # Create module file after installation.
   create_module_file(version, install_dir)
   update_bashrc()

   print(f"GCC version {version} has been installed successfully in {install_dir}.")
   print(f"Module file created at ~/compiler_modulefiles/gcc/gcc-{version}.")

if __name__ == "__main__":
   main()
