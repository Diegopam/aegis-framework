#!/usr/bin/env python3
"""
Aegis Builder - AppImage Packaging System

Creates lightweight AppImages from Aegis projects.
"""

import os
import sys
import json
import shutil
import stat
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional


class AegisBuilder:
    """
    Builds AppImages from Aegis projects
    """
    
    APPIMAGETOOL_URL = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    
    def __init__(self, project_dir: str = '.'):
        self.project_dir = Path(project_dir).resolve()
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load project configuration"""
        config_path = self.project_dir / 'aegis.config.json'
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}
    
    def build(self, output_dir: str = 'dist', name: Optional[str] = None) -> str:
        """
        Build the AppImage
        
        Args:
            output_dir: Output directory for the AppImage
            name: Custom name for the AppImage
            
        Returns:
            Path to the created AppImage
        """
        app_name = name or self.config.get('name', 'AegisApp')
        output_path = Path(output_dir).resolve()
        appdir = output_path / f'{app_name}.AppDir'
        
        print(f"📦 Building: {app_name}")
        
        # Clean and create AppDir
        if appdir.exists():
            shutil.rmtree(appdir)
        appdir.mkdir(parents=True)
        
        # Create AppDir structure
        self._create_appdir_structure(appdir, app_name)
        
        # Copy project files
        self._copy_project_files(appdir)
        
        # Copy Aegis runtime
        self._copy_aegis_runtime(appdir)
        
        # Create AppRun script
        self._create_apprun(appdir, app_name)
        
        # Create .desktop file
        self._create_desktop_file(appdir, app_name)
        
        # Create icon
        self._create_icon(appdir, app_name)
        
        # Download appimagetool if needed
        appimagetool = self._ensure_appimagetool(output_path)
        
        # Build AppImage
        appimage_path = output_path / f'{app_name}-x86_64.AppImage'
        self._build_appimage(appdir, appimage_path, appimagetool)
        
        return str(appimage_path)
    
    def _create_appdir_structure(self, appdir: Path, app_name: str):
        """Create AppDir directory structure"""
        dirs = [
            'usr/bin',
            'usr/lib/aegis',
            'usr/share/applications',
            'usr/share/icons/hicolor/256x256/apps',
            'usr/share/aegis/runtime',
            'app'
        ]
        for d in dirs:
            (appdir / d).mkdir(parents=True, exist_ok=True)
        
        print("  📁 Created AppDir structure")
    
    def _copy_project_files(self, appdir: Path):
        """Copy project files to AppDir"""
        app_dir = appdir / 'app'
        
        # Copy all project files except dist, __pycache__, etc.
        exclude = {'.git', '__pycache__', 'dist', '.venv', 'node_modules', '*.AppDir'}
        
        for item in self.project_dir.iterdir():
            if item.name in exclude or item.suffix == '.AppDir':
                continue
            
            dest = app_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns(*exclude))
            else:
                shutil.copy2(item, dest)
        
        print("  📄 Copied project files")
    
    def _copy_aegis_runtime(self, appdir: Path):
        """Copy Aegis runtime files"""
        aegis_dir = Path(__file__).parent.parent
        runtime_dir = appdir / 'usr/share/aegis'
        
        # Create directory
        runtime_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy core modules
        shutil.copytree(
            aegis_dir / 'core',
            runtime_dir / 'core',
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'),
            dirs_exist_ok=True
        )
        
        # Copy runtime (JS API)
        shutil.copytree(
            aegis_dir / 'runtime',
            runtime_dir / 'runtime',
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'),
            dirs_exist_ok=True
        )
        
        # Create __init__.py
        init_content = '''"""Aegis Runtime"""
from aegis.core.aegis import AegisApp
'''
        with open(runtime_dir / '__init__.py', 'w') as f:
            f.write(init_content)
        
        print("  ⚡ Copied Aegis runtime")
    
    def _create_apprun(self, appdir: Path, app_name: str):
        """Create AppRun script"""
        apprun_content = '''#!/bin/bash
# Aegis AppRun Script

# Get the directory where AppImage is mounted
APPDIR="$(dirname "$(readlink -f "$0")")"

# Set up Python path
export PYTHONPATH="$APPDIR/usr/share:$PYTHONPATH"

# Change to app directory
cd "$APPDIR/app"

# Run Aegis app
exec python3 -c "
import sys
sys.path.insert(0, '$APPDIR/usr/share')
from aegis.core.aegis import AegisApp
app = AegisApp()
app.run()
"
'''
        apprun_path = appdir / 'AppRun'
        with open(apprun_path, 'w') as f:
            f.write(apprun_content)
        
        # Make executable
        apprun_path.chmod(apprun_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        
        print("  🚀 Created AppRun script")
    
    def _create_desktop_file(self, appdir: Path, app_name: str):
        """Create .desktop file"""
        desktop_content = f'''[Desktop Entry]
Type=Application
Name={self.config.get('title', app_name)}
Exec=AppRun
Icon={app_name.lower()}
Categories=Utility;
Comment={self.config.get('description', 'An Aegis application')}
Terminal=false
'''
        # Write to AppDir root and usr/share/applications
        for path in [appdir / f'{app_name}.desktop', 
                     appdir / 'usr/share/applications' / f'{app_name}.desktop']:
            with open(path, 'w') as f:
                f.write(desktop_content)
        
        print("  📋 Created .desktop file")
    
    def _create_icon(self, appdir: Path, app_name: str):
        """Create or copy app icon"""
        icon_source = self.project_dir / self.config.get('icon', 'assets/icon.png')
        
        if icon_source.exists():
            # Copy existing icon
            shutil.copy2(icon_source, appdir / f'{app_name.lower()}.png')
            shutil.copy2(
                icon_source, 
                appdir / 'usr/share/icons/hicolor/256x256/apps' / f'{app_name.lower()}.png'
            )
            print("  🎨 Copied app icon")
        else:
            # Create a simple placeholder icon (1x1 transparent PNG)
            # In production, you'd want to generate a proper icon
            placeholder = appdir / f'{app_name.lower()}.png'
            self._create_placeholder_icon(placeholder)
            shutil.copy2(
                placeholder,
                appdir / 'usr/share/icons/hicolor/256x256/apps' / f'{app_name.lower()}.png'
            )
            print("  🎨 Created placeholder icon")
    
    def _create_placeholder_icon(self, path: Path):
        """Create a simple placeholder PNG icon"""
        # Minimal valid PNG (1x1 transparent pixel)
        # In a real scenario, we'd generate a proper icon with cairo or PIL
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
            0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
            0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
            0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
            0x42, 0x60, 0x82
        ])
        with open(path, 'wb') as f:
            f.write(png_data)
    
    def _ensure_appimagetool(self, output_path: Path) -> Path:
        """Download appimagetool if not present"""
        tool_path = output_path / 'appimagetool'
        
        if not tool_path.exists():
            print("  📥 Downloading appimagetool...")
            urllib.request.urlretrieve(self.APPIMAGETOOL_URL, tool_path)
            tool_path.chmod(tool_path.stat().st_mode | stat.S_IXUSR)
        
        return tool_path
    
    def _build_appimage(self, appdir: Path, output: Path, appimagetool: Path):
        """Build the final AppImage"""
        print("  🔨 Building AppImage...")
        
        env = os.environ.copy()
        env['ARCH'] = 'x86_64'
        
        result = subprocess.run(
            [str(appimagetool), str(appdir), str(output)],
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  ❌ appimagetool error: {result.stderr}")
            raise RuntimeError(f"appimagetool failed: {result.stderr}")
        
        # Clean up AppDir
        shutil.rmtree(appdir)
        
        print(f"  ✅ AppImage created: {output.name}")


def build_project(project_dir: str = '.', output_dir: str = 'dist', name: str = None) -> str:
    """
    Convenience function to build a project
    
    Args:
        project_dir: Path to the project
        output_dir: Output directory
        name: Custom AppImage name
        
    Returns:
        Path to the created AppImage
    """
    builder = AegisBuilder(project_dir)
    return builder.build(output_dir, name)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        build_project(sys.argv[1])
    else:
        build_project()
