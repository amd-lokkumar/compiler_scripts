#!/usr/bin/python3

import os
import subprocess
import sys

def usage():
    print("Usage: python install_llvm.py [version]")
    print("Example: python install_llvm.py 19.1.3")
    sys.exit(1)

def check_command(command):
    return subprocess.call(f"command -v {command}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def install_packages():
    print("Installing required packages...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "build-essential", "cmake", "git", "-y"], check=True)
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

def clone_llvm(version):
    print(f"Cloning LLVM version {version}...")
    try:
        subprocess.run([
            "git", "clone", "--depth", "1",
            f"--branch=llvmorg-{version}",
            "https://github.com/llvm/llvm-project.git"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error cloning LLVM: {e}")
        sys.exit(1)

def build_llvm(install_dir):
    print("Configuring LLVM...")
    
    try:
        os.makedirs("llvm-project/build", exist_ok=True)
        
        subprocess.run([
            "cmake",
            "-S", "llvm-project/llvm",
            "-B", "llvm-project/build",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DLLVM_ENABLE_PROJECTS=clang;lld;flang;openmp;clang-tools-extra"
        ], check=True)

        print("Building LLVM... This may take some time.")
        subprocess.run(["cmake", "--build", "llvm-project/build", "-j32"], check=True)  # Use a fixed number of jobs

        print("Installing LLVM...")
        subprocess.run(["cmake", "--install", "llvm-project/build", "--prefix", install_dir], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error during build process: {e}")
        sys.exit(1)

def copy_openmp_library(install_dir):
    source_libomp = os.path.join(install_dir, 'lib', 'x86_64-unknown-linux-gnu', 'libomp.so')
    destination_libomp = os.path.join(install_dir, 'lib', 'libomp.so')

    try:
        if os.path.isfile(source_libomp):
            subprocess.run(['cp', source_libomp, destination_libomp], check=True)
            print(f"Copied libomp.so from {source_libomp} to {destination_libomp}.")
        else:
            print(f"Source library {source_libomp} does not exist.")
    except Exception as e:
        print(f"Error copying OpenMP library: {e}")
        sys.exit(1)

def create_module_file(version, install_dir):
    modulefile_dir = os.path.expanduser(f"~/compiler_modulefiles/llvm")
    os.makedirs(modulefile_dir, exist_ok=True)
    
    modulefile_path = os.path.join(modulefile_dir, f"llvm-{version}")
    
    try:
        with open(modulefile_path, 'w') as f:
            f.write(f"""#%Module1.0

proc ModulesHelp {{ }} {{
    global version modroot
    puts stderr "LLVM version {version} - sets the environment for llvm-{version}"
}}

module-whatis "Sets the environment for LLVM version {version}"

set topdir {install_dir}
set version {version}

setenv CC ${{topdir}}/bin/clang
setenv CXX ${{topdir}}/bin/clang++
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
   
   # Default to 19.1.3 if no version is provided
   if not version:
       version = "19.1.3"
   
   install_dir = os.path.expanduser(f"~/compiler_installation/llvm-{version}")

   # Check if LLVM is already installed
   if os.path.isfile(os.path.join(install_dir, 'bin', 'clang')):
       print(f"LLVM version {version} is already installed in {install_dir}.")
       
       create_module_file(version, install_dir)
       update_bashrc()
       
       return

   # Create installation directory
   os.makedirs(install_dir, exist_ok=True)

   # Install required packages
   install_packages()

   # Install environment modules
   install_environment_modules()

   # Clone the LLVM repository.
   clone_llvm(version)

   # Build and install LLVM.
   build_llvm(version, install_dir)

   # Copy OpenMP library after installation.
   copy_openmp_library(install_dir)

   # Create module file after installation.
   create_module_file(version, install_dir)
   update_bashrc()

   print(f"LLVM version {version} has been installed successfully in {install_dir}.")
   print(f"Module file created at ~/compiler_modulefiles/llvm/llvm-{version}.")

if __name__ == "__main__":
   main()
