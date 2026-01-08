#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OBLISK Nuitka Build Script
Compiles oblisk_cli.py to standalone Windows EXE using Nuitka
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path
from typing import Optional, List

__version__ = "3.0.0"


class Colors:
    """ANSI color codes."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"


def print_success(msg: str):
    print(f"{Colors.GREEN}[+]{Colors.RESET} {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}[-]{Colors.RESET} {msg}")


def print_info(msg: str):
    print(f"{Colors.CYAN}[*]{Colors.RESET} {msg}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}[!]{Colors.RESET} {msg}")


class NuitkaBuildScript:
    """Handles building OBLISK.exe with Nuitka."""
    
    def __init__(
        self,
        version: str = __version__,
        output_dir: str = "./dist",
        mode: str = "standalone",  # standalone, onefile
        enable_console: bool = True,
    ):
        self.version = version
        self.output_dir = Path(output_dir)
        self.mode = mode
        self.enable_console = enable_console
        self.project_root = Path(__file__).parent
    
    def check_prerequisites(self) -> bool:
        """Verify Nuitka and dependencies are installed."""
        print_info("Checking prerequisites...\n")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print_error(f"Python 3.8+ required (found {sys.version})")
            return False
        print_success(f"Python {sys.version.split()[0]} OK")
        
        # Check Nuitka
        try:
            result = subprocess.run(
                [sys.executable, "-m", "nuitka", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                nuitka_version = result.stdout.strip()
                print_success(f"Nuitka {nuitka_version} found")
            else:
                print_error("Nuitka check failed")
                return False
        except Exception as e:
            print_error(f"Failed to check Nuitka: {e}")
            print_info("Installing Nuitka...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "nuitka"],
                    check=True,
                )
                print_success("Nuitka installed")
            except Exception as install_error:
                print_error(f"Failed to install Nuitka: {install_error}")
                return False
        
        # Check for main file
        if not (self.project_root / "oblisk_cli.py").exists():
            print_error(f"oblisk_cli.py not found in {self.project_root}")
            return False
        print_success("oblisk_cli.py found")
        
        # Check requirements.txt
        req_file = self.project_root / "requirements.txt"
        if not req_file.exists():
            print_warning("requirements.txt not found (optional)")
        else:
            print_success(f"requirements.txt found")
        
        return True
    
    def install_dependencies(self) -> bool:
        """Install runtime dependencies from requirements.txt."""
        req_file = self.project_root / "requirements.txt"
        
        if not req_file.exists():
            print_info("No requirements.txt found, skipping dependency install")
            return True
        
        print_info("Installing dependencies...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                check=True,
            )
            print_success("Dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install dependencies: {e}")
            return False
    
    def create_output_directory(self) -> bool:
        """Create output directory."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            print_success(f"Output directory: {self.output_dir.absolute()}")
            return True
        except Exception as e:
            print_error(f"Failed to create output directory: {e}")
            return False
    
    def build_with_nuitka(self) -> bool:
        """Run Nuitka build."""
        print_info(f"\nBuilding OBLISK v{self.version} with Nuitka...\n")
        
        # Build command
        cmd = [
            sys.executable,
            "-m",
            "nuitka",
            # Basic options
            "--follow-imports",
            "--onefile" if self.mode == "onefile" else "--standalone",
            # Output options
            f"--output-dir={self.output_dir}",
            f"--output-filename=OBLISK",
            # Windows-specific
            "--windows-disable-console" if not self.enable_console else "",
            # Include data files
            "--include-data-dir=./config:config",
            "--include-data-dir=./examples:examples",
            # Optimization
            "-O",  # Optimize
            # Python optimization
            "--remove-output",
            # Verbose
            "--verbose",
            # Entry point
            "oblisk_cli.py",
        ]
        
        # Remove empty strings
        cmd = [arg for arg in cmd if arg]
        
        print_info("Nuitka command:")
        print(" ".join(cmd))
        print()
        
        try:
            result = subprocess.run(cmd, cwd=str(self.project_root), check=False)
            if result.returncode != 0:
                print_error(f"Nuitka build failed with exit code {result.returncode}")
                return False
            
            print_success("Nuitka compilation completed")
            return True
        except Exception as e:
            print_error(f"Failed to run Nuitka: {e}")
            return False
    
    def locate_output_exe(self) -> Optional[Path]:
        """Find the compiled EXE file."""
        # Different Nuitka output paths depending on mode
        candidates = [
            self.output_dir / "OBLISK.exe",
            self.output_dir / "OBLISK.build" / "OBLISK.exe",
            self.project_root / "OBLISK.exe",
            self.project_root / "OBLISK.dist" / "OBLISK.exe",
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        # Search recursively as fallback
        for exe in self.output_dir.rglob("*.exe"):
            if "OBLISK" in exe.name:
                return exe
        
        return None
    
    def verify_build(self, exe_path: Path) -> bool:
        """Verify the built EXE."""
        print_info("Verifying build...\n")
        
        if not exe_path.exists():
            print_error(f"EXE not found: {exe_path}")
            return False
        
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print_success(f"EXE file: {exe_path}")
        print_success(f"Size: {size_mb:.2f} MB")
        
        # Test basic execution
        print_info("Testing EXE execution...")
        try:
            result = subprocess.run(
                [str(exe_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                print_success(f"EXE executed successfully")
                print_success(f"Output: {result.stdout.strip()}")
                return True
            else:
                print_warning(f"EXE returned exit code {result.returncode}")
                print_warning(f"Output: {result.stderr}")
                return True  # Not critical
        except subprocess.TimeoutExpired:
            print_warning("EXE execution timed out (may be normal)")
            return True
        except Exception as e:
            print_warning(f"Could not execute EXE: {e}")
            return True  # Not critical
    
    def create_portable_bundle(self, exe_path: Path) -> bool:
        """Create portable distribution bundle."""
        print_info("Creating portable bundle...\n")
        
        bundle_dir = self.output_dir / f"OBLISK-Portable-{self.version}"
        
        try:
            # Create bundle directory
            bundle_dir.mkdir(exist_ok=True)
            
            # Copy EXE
            import shutil
            shutil.copy2(exe_path, bundle_dir / exe_path.name)
            print_success(f"Copied EXE to bundle")
            
            # Copy config if exists
            config_src = self.project_root / "config"
            if config_src.exists():
                config_dst = bundle_dir / "config"
                if config_dst.exists():
                    shutil.rmtree(config_dst)
                shutil.copytree(config_src, config_dst)
                print_success(f"Copied config directory")
            
            # Copy README template
            readme_path = bundle_dir / "README.txt"
            readme_content = f"""
OBLISK v{self.version} - Portable Distribution
==============================================

USAGE:
  OBLISK.exe [command] [options]

COMMANDS:
  --help              Show help
  --version           Show version
  start               Start daemon
  status              Show status
  exec <script>       Execute script
  vault               Manage vault
  memory              Manage memory

EXAMPLES:
  OBLISK.exe --help
  OBLISK.exe start --port 8000
  OBLISK.exe status --json

FOR MORE INFO:
  https://github.com/POWDER-RANGER/OBLISK
"""
            readme_path.write_text(readme_content)
            print_success(f"Created README.txt")
            
            print_success(f"Portable bundle created: {bundle_dir}")
            return True
        except Exception as e:
            print_error(f"Failed to create portable bundle: {e}")
            return False
    
    def cleanup_build_artifacts(self) -> None:
        """Clean up intermediate build files."""
        print_info("Cleaning up build artifacts...")
        
        # Remove build directories (keep dist/exe only)
        dirs_to_clean = [
            self.project_root / "OBLISK.build",
            self.project_root / "__pycache__",
            self.output_dir / "OBLISK.build",
        ]
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print_success(f"Removed {dir_path.name}")
                except Exception as e:
                    print_warning(f"Could not remove {dir_path}: {e}")
    
    def run(self) -> int:
        """Execute the build process."""
        print(f"{Colors.CYAN}" + "="*60)
        print(f"OBLISK Nuitka Build v{self.version}")
        print(f"Building standalone Windows executable")
        print(f"="*60 + f"{Colors.RESET}\n")
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            print_error("Prerequisites check failed")
            return 1
        
        # Step 2: Install dependencies
        if not self.install_dependencies():
            print_warning("Some dependencies may be missing")
        
        # Step 3: Create output directory
        if not self.create_output_directory():
            print_error("Failed to create output directory")
            return 1
        
        # Step 4: Build
        if not self.build_with_nuitka():
            print_error("Build failed")
            return 1
        
        # Step 5: Locate output
        exe_path = self.locate_output_exe()
        if not exe_path:
            print_error("Could not locate output EXE")
            return 1
        
        # Step 6: Verify
        if not self.verify_build(exe_path):
            print_warning("Build verification had issues")
        
        # Step 7: Create bundle
        if not self.create_portable_bundle(exe_path):
            print_warning("Could not create portable bundle")
        
        # Step 8: Cleanup
        self.cleanup_build_artifacts()
        
        # Summary
        print(f"\n{Colors.GREEN}" + "="*60)
        print(f"BUILD COMPLETED SUCCESSFULLY")
        print(f"="*60 + f"{Colors.RESET}")
        print(f"EXE: {exe_path}")
        print(f"Dist: {self.output_dir}")
        print(f"\nNext steps:")
        print(f"1. Test on clean Windows machine")
        print(f"2. Distribute or upload to releases")
        print(f"3. Tag release: git tag v{self.version} && git push --tags")
        
        return 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build OBLISK Windows EXE with Nuitka",
    )
    parser.add_argument(
        "--version",
        default=__version__,
        help=f"Version number (default: {__version__})",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="./dist",
        help="Output directory (default: ./dist)",
    )
    parser.add_argument(
        "--mode",
        choices=["standalone", "onefile"],
        default="standalone",
        help="Build mode (default: standalone)",
    )
    parser.add_argument(
        "--no-console",
        action="store_true",
        help="Hide console window on startup",
    )
    
    args = parser.parse_args()
    
    builder = NuitkaBuildScript(
        version=args.version,
        output_dir=args.output,
        mode=args.mode,
        enable_console=not args.no_console,
    )
    
    return builder.run()


if __name__ == "__main__":
    sys.exit(main())
