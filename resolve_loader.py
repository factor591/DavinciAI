import sys
import os
import logging
import platform

def get_fusion_script_paths():
    """Return potential paths for fusionscript.dll/so based on OS and common locations."""
    paths = []
    
    # Check environment variables first
    env_path = os.getenv("RESOLVE_SCRIPT_LIB")
    if env_path:
        paths.append(env_path)
    
    # Check operating system
    if platform.system() == "Windows":
        # Standard Resolve installation paths on Windows
        paths.extend([
            "C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\fusionscript.dll",
            "C:\\Program Files\\Blackmagic Design\\DaVinci Resolve Studio\\fusionscript.dll",
            # Add the ProgramData path which might contain the Scripting directory
            os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 
                         "Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules\\fusionscript.dll")
        ])
        
        # Add to PATH temporarily
        for potential_path in paths:
            if os.path.exists(os.path.dirname(potential_path)):
                if os.path.dirname(potential_path) not in os.environ['PATH']:
                    os.environ['PATH'] = os.path.dirname(potential_path) + os.pathsep + os.environ['PATH']
                    logging.info("Added %s to PATH", os.path.dirname(potential_path))
                
    elif platform.system() == "Darwin":  # macOS
        paths.extend([
            "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so",
            "/Applications/DaVinci Resolve Studio/DaVinci Resolve Studio.app/Contents/Libraries/Fusion/fusionscript.so"
        ])
    elif platform.system() == "Linux":
        paths.extend([
            "/opt/resolve/libs/Fusion/fusionscript.so",
            "/opt/resolve/libs/fusionscript.so"
        ])
    
    return paths

def load_resolve_script():
    """Attempt to load the DaVinci Resolve scripting module using multiple strategies."""
    logging.info("Attempting to load DaVinci Resolve scripting module...")
    
    # First try direct import
    try:
        import fusionscript as script_module
        logging.info("Successfully imported fusionscript module directly.")
        return script_module
    except ImportError as e:
        logging.warning("Could not directly import fusionscript: %s", e)
    
    # Next try adding Resolve scripting module paths to Python path
    module_paths = [
        os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 
                     "Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules"),
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",  # macOS
        "/opt/resolve/Developer/Scripting/Modules"  # Linux
    ]
    
    for path in module_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.append(path)
            logging.info("Added %s to Python path", path)
    
    # Try import again after path additions
    try:
        import fusionscript as script_module
        logging.info("Successfully imported fusionscript after adding module paths.")
        return script_module
    except ImportError:
        logging.warning("Still could not import fusionscript after adding module paths.")
    
    # As a last resort, try dynamic loading with potential paths
    fusion_paths = get_fusion_script_paths()
    for path in fusion_paths:
        if os.path.exists(path):
            logging.info("Found fusionscript at: %s", path)
            try:
                script_module = load_dynamic("fusionscript", path)
                logging.info("Successfully loaded fusionscript dynamically from %s", path)
                return script_module
            except Exception as e:
                logging.warning("Failed to load %s: %s", path, e)
    
    logging.critical("Could not locate fusionscript module. Ensure DaVinci Resolve is installed.")
    return None

def load_dynamic(module_name, file_path):
    """Load a dynamic module (.dll/.so) based on Python version."""
    if sys.version_info[0] >= 3 and sys.version_info[1] >= 5:
        import importlib.machinery
        import importlib.util
        
        module = None
        loader = importlib.machinery.ExtensionFileLoader(module_name, file_path)
        if loader:
            spec = importlib.util.spec_from_loader(module_name, loader)
            if spec:
                module = importlib.util.module_from_spec(spec)
                if module:
                    loader.exec_module(module)
        return module
    else:
        import imp
        return imp.load_dynamic(module_name, file_path)