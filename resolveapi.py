import sys

# Adjust path to point to your Resolve Scripting Modules if needed:
sys.path.append("C:\\ProgramData\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules")

try:
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")

    if resolve:
        print("Successfully connected to DaVinci Resolve API!")
    else:
        print("Failed to connect to DaVinci Resolve.")

except ImportError as e:
    print(f"Error: {e}")
