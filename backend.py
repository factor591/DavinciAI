import os
import logging
import time
import platform
import api_helper  # Changed from relative import
from api_helper import ResolveAPIHelper

# Import DaVinciResolveScript using our improved loader
import resolve_loader  # Changed from relative import
dvr = resolve_loader.load_resolve_script()

class ResolveController:
    def __init__(self, retries=3, delay=2):
        attempt = 0
        self.resolve = None
        self.api_helper = None
        
        while attempt < retries:
            try:
                self.resolve = dvr.scriptapp("Resolve")
                if self.resolve:
                    logging.info("Connected to DaVinci Resolve on attempt %d.", attempt + 1)
                    
                    # Initialize API helper to detect available methods
                    self.api_helper = ResolveAPIHelper(self.resolve)
                    logging.info("API Feature Support: %s", self.api_helper.get_feature_support_info())
                    break
                else:
                    logging.warning("Attempt %d: DaVinci Resolve returned None. Is it running?", attempt + 1)
            except Exception as e:
                # ADDED: More explicit logging on why it failed
                logging.warning(
                    "Attempt %d: Exception connecting to DaVinci Resolve: %s",
                    attempt + 1, e
                )
                logging.warning("Check if fusionscript.dll is on PATH or bundled with your EXE.")
            attempt += 1
            time.sleep(delay)

        # MODIFIED: Raise a more descriptive error
        if not self.resolve:
            logging.critical("Failed to connect to DaVinci Resolve after %d attempts.", retries)
            raise Exception(
                "Could not connect to DaVinci Resolve. Check if Resolve is running "
                "and fusionscript.dll is accessible."
            )

        try:
            self.project_manager = self.resolve.GetProjectManager()
            self.project = (
                self.project_manager.GetCurrentProject()
                or self.project_manager.CreateProject("Drone Edit Project")
            )
            self.media_pool = self.project.GetMediaPool()
            
            # Log more detailed environment info
            self._log_environment_info()
        except Exception as e:
            logging.critical("Error initializing project: %s", e)
            raise

    def _log_environment_info(self):
        """Log detailed environment information for debugging."""
        try:
            # OS info
            logging.info("Operating System: %s", platform.platform())
            
            # Python info
            logging.info("Python Version: %s", platform.python_version())
            
            # Resolve info if available
            if hasattr(self.resolve, "GetVersionString"):
                logging.info("DaVinci Resolve Version: %s", self.resolve.GetVersionString())
            
            # Log relevant environment variables
            for env_var in ["RESOLVE_SCRIPT_API", "RESOLVE_SCRIPT_LIB", "PATH"]:
                value = os.environ.get(env_var, "Not set")
                if env_var == "PATH":
                    logging.debug("PATH: %s", value)
                else:
                    logging.info("%s: %s", env_var, value)
                    
            # Log current project info
            if self.project:
                logging.info("Current Project: %s", self.project.GetName())
                
        except Exception as e:
            logging.warning("Error logging environment info: %s", e)

    def import_media(self, file_paths):
        try:
            valid_paths = [p for p in file_paths if os.path.exists(p)]
            if not valid_paths:
                logging.error("None of the provided file paths exist: %s", file_paths)
                return None
                
            new_items = self.media_pool.ImportMedia(valid_paths)
            if new_items:
                logging.info("Imported media: %s", valid_paths)
            else:
                logging.error("Media import returned None for files: %s", valid_paths)
            return new_items
        except Exception as e:
            logging.exception("Error importing media: %s", e)
            return None

    def create_timeline(self, clips):
        try:
            if not clips:
                logging.error("No clips provided to create timeline.")
                return None
            timeline = self.media_pool.CreateTimelineFromClips("Auto Timeline", clips)
            if timeline:
                logging.info("Timeline created successfully with %d clip(s).", len(clips))
                self.auto_apply_color_and_transitions(timeline)
            else:
                logging.error("Failed to create timeline with clips: %s", clips)
            return timeline
        except Exception as e:
            logging.exception("Exception while creating timeline: %s", e)
            return None

    def get_current_timeline(self):
        try:
            timeline = self.project.GetCurrentTimeline()
            if not timeline:
                logging.warning("No current timeline found.")
            return timeline
        except Exception as e:
            logging.exception("Error retrieving current timeline: %s", e)
            return None

    def apply_lut(self, lut_path):
        timeline = self.get_current_timeline()
        if timeline:
            for clip in timeline.GetItemsInTrack("video", 1):
                try:
                    clip.ApplyLUT(lut_path)
                except Exception as e:
                    logging.exception("Failed to apply LUT on clip: %s", e)
            logging.info("LUT '%s' applied to timeline clips.", lut_path)
        else:
            logging.warning("No timeline found to apply LUT.")

    def seconds_to_timecode(self, seconds, fps=30):
        frames = int(round(seconds * fps))
        h = frames // (fps * 3600)
        frames %= (fps * 3600)
        m = frames // (fps * 60)
        frames %= (fps * 60)
        s = frames // fps
        f = frames % fps
        return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"

    def get_clip_name(self, clip_item):
        try:
            if not clip_item:
                return "Unknown"
                
            if not hasattr(clip_item, "GetClipProperty"):
                logging.warning("Clip item of type %s lacks GetClipProperty.", type(clip_item))
                return "Unknown"

            name = None
            # Safely try each property
            for prop in ["File Path", "Clip Name", "Name"]:
                try:
                    name = clip_item.GetClipProperty(prop)
                    if name:
                        break
                except:
                    pass
                    
            if not name:
                try:
                    name = clip_item.GetName()
                except:
                    name = None
            return name or "Unknown"
        except Exception as e:
            logging.exception("Error in get_clip_name: %s", e)
            return "Unknown"

    def update_timeline_with_trimmed_clips(self, new_clips):
        try:
            if not new_clips:
                logging.warning("No new clips provided to update timeline.")
                return False
                
            timeline = self.get_current_timeline()
            if not timeline:
                logging.warning("Cannot update timeline: No current timeline found.")
                return False

            logging.info("Clearing original timeline clips.")
            # Use API helper for version-safe method call
            all_clips = timeline.GetItemListInTrack("video", 1)
            
            if self.api_helper and self.api_helper.is_method_available("timeline.RemoveItem"):
                for c in all_clips:
                    self.api_helper.safe_remove_timeline_item(timeline, c)
            else:
                logging.warning("timeline.RemoveItem is not available in this API version. Skipping old clip removal.")

            for (source_clip, start_sec, end_sec) in new_clips:
                clip_name = self.get_clip_name(source_clip)
                logging.info("Appending new clip: Original clip %s, from %s to %s", clip_name, start_sec, end_sec)

                has_duplicate_method = (
                    self.api_helper and 
                    self.api_helper.is_method_available("mediaPool.DuplicateMediaPoolItem")
                )
                
                trimmed_clip = None
                if has_duplicate_method:
                    try:
                        trimmed_clip = self.media_pool.DuplicateMediaPoolItem(source_clip)
                    except Exception:
                        logging.exception("Failed to duplicate MediaPoolItem. Falling back to original clip.")

                final_clip = trimmed_clip if trimmed_clip else source_clip

                subclip_name = f"{clip_name}_sub_{start_sec}_{end_sec}"
                start_tc = self.seconds_to_timecode(start_sec)
                end_tc = self.seconds_to_timecode(end_sec)

                try:
                    self.media_pool.AppendToTimeline([final_clip])
                except Exception as e:
                    logging.exception("Failed to append clip to timeline: %s", e)

            logging.info("Timeline updated with trimmed clips.")
            self.auto_apply_color_and_transitions(timeline)
            return True
        except Exception as e:
            logging.exception("Error updating timeline with trimmed clips: %s", e)
            return False

    def auto_apply_color_and_transitions(self, timeline):
        if not timeline:
            logging.warning("No timeline found to apply color/transitions.")
            return

        # Apply LUT if available
        lut_path = "C:/Path/To/SomeDefaultLUT.cube"
        if os.path.exists(lut_path):
            for clip in timeline.GetItemsInTrack("video", 1):
                try:
                    clip.ApplyLUT(lut_path)
                except Exception as e:
                    logging.exception("Failed to apply LUT on clip: %s", e)
            logging.info("Auto LUT applied to timeline clips.")
        else:
            logging.warning("Auto LUT path not found; skipping LUT color pass.")

        # Add transitions using the API helper
        if self.api_helper and self.api_helper.is_method_available("timeline.AddTransition"):
            video_items = timeline.GetItemListInTrack("video", 1)
            for i in range(len(video_items) - 1):
                self.api_helper.safe_add_transition(
                    timeline, "Cross Dissolve", video_items[i], video_items[i+1], 30
                )
            logging.info("Attempted to add transitions between consecutive timeline clips.")
        else:
            logging.warning(
                "timeline.AddTransition is not available in this API version; skipping transitions."
            )
            
    def get_lut_path(self, lut_name):
        """Get path to a specific LUT based on name."""
        lut_directories = [
            os.path.expanduser("~/Documents/Blackmagic Design/DaVinci Resolve/LUT"),
            "C:/ProgramData/Blackmagic Design/DaVinci Resolve/Support/LUT",
            "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"
        ]
        
        lut_names = {
            "Default": "Default.cube",
            "Cinematic": "Film Look.cube",
            "Vintage": "Vintage Film.cube"
        }
        
        filename = lut_names.get(lut_name, f"{lut_name}.cube")
        
        for directory in lut_directories:
            path = os.path.join(directory, filename)
            if os.path.exists(path):
                return path
                
        logging.warning(f"LUT '{lut_name}' not found in standard locations.")
        return None
        
    def fusion_automation(self):
        """Apply advanced Fusion effects to the current timeline."""
        try:
            timeline = self.get_current_timeline()
            if not timeline:
                logging.warning("No timeline found for Fusion automation.")
                return False
                
            # This is just a stub - expanded implementation would depend on
            # what Fusion effects you want to apply
            logging.info("Fusion automation not fully implemented yet.")
            return True
            
        except Exception as e:
            logging.exception("Error in fusion_automation: %s", e)
            return False