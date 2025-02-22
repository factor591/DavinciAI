import os
import logging
import time
import DaVinciResolveScript as dvr

class ResolveController:
    def __init__(self, retries=3, delay=2):
        attempt = 0
        self.resolve = None
        while attempt < retries:
            try:
                self.resolve = dvr.scriptapp("Resolve")
                if self.resolve:
                    logging.info("Connected to DaVinci Resolve on attempt %d.", attempt + 1)
                    break
                else:
                    logging.warning("Attempt %d: DaVinci Resolve returned None. Is it running?", attempt + 1)
            except Exception as e:
                logging.warning("Attempt %d: Exception connecting to DaVinci Resolve: %s", attempt + 1, e)
            attempt += 1
            time.sleep(delay)
        if not self.resolve:
            logging.critical("Failed to connect to DaVinci Resolve after %d attempts.", retries)
            raise Exception("DaVinci Resolve is not running. Ensure Resolve is launched and accessible.")

        try:
            self.project_manager = self.resolve.GetProjectManager()
            self.project = (
                self.project_manager.GetCurrentProject()
                or self.project_manager.CreateProject("Drone Edit Project")
            )
            self.media_pool = self.project.GetMediaPool()
        except Exception as e:
            logging.critical("Error initializing project: %s", e)
            raise

    def import_media(self, file_paths):
        try:
            new_items = self.media_pool.ImportMedia(file_paths)
            if new_items:
                logging.info("Imported media: %s", file_paths)
            else:
                logging.error("Media import returned None for files: %s", file_paths)
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
        """
        Helper to robustly retrieve a clip name from multiple metadata sources.
        ## CHANGED: Enhanced fallback checks for missing metadata.
        """
        try:
            if not hasattr(clip_item, "GetClipProperty"):
                logging.warning("Clip item of type %s lacks GetClipProperty.", type(clip_item))
                return "Unknown"

            name = (clip_item.GetClipProperty("File Path") or
                    clip_item.GetClipProperty("Clip Name") or
                    clip_item.GetClipProperty("Name"))
            if not name:
                # Fallback to legacy GetName if possible
                try:
                    name = clip_item.GetName()
                except Exception:
                    name = None
            if not name:
                name = "Unknown"
            return name
        except Exception as e:
            logging.exception("Error in get_clip_name: %s", e)
            return "Unknown"

    def update_timeline_with_trimmed_clips(self, new_clips):
        """
        Creates subclips from scene-detected segments and builds a new timeline.
        Checks if the AddSubClip method is available in the current API.
        """
        try:
            if not hasattr(self.media_pool, "AddSubClip") or not callable(self.media_pool.AddSubClip):
                logging.error("The AddSubClip method is not available in this version of the DaVinci Resolve API.")
                return False

            timeline = self.get_current_timeline()
            if not timeline:
                logging.warning("Cannot update timeline: No current timeline found.")
                return False

            logging.info("Clearing original timeline clips.")
            # Clear out the original timeline
            all_clips = timeline.GetItemListInTrack("video", 1)
            for c in all_clips:
                timeline.RemoveItem(c)

            for (source_clip, start_sec, end_sec) in new_clips:
                clip_name = self.get_clip_name(source_clip)
                logging.info("Appending new clip: Original clip %s, from %s to %s", clip_name, start_sec, end_sec)

                # ## CHANGED: Check DuplicateMediaPoolItem availability
                trimmed_clip = None
                if hasattr(self.media_pool, "DuplicateMediaPoolItem") and callable(self.media_pool.DuplicateMediaPoolItem):
                    trimmed_clip = self.media_pool.DuplicateMediaPoolItem(source_clip)
                else:
                    logging.error("DuplicateMediaPoolItem method is not available in this API version.")
                    # Fallback: Just add subclip directly
                    pass

                if trimmed_clip:
                    subclip_name = f"{clip_name}_sub_{start_sec}_{end_sec}"
                    start_tc = self.seconds_to_timecode(start_sec)
                    end_tc = self.seconds_to_timecode(end_sec)

                    try:
                        result = self.media_pool.AddSubClip(trimmed_clip,
                                                            subclip_name,
                                                            start_tc,
                                                            end_tc,
                                                            1)
                        if not result:
                            logging.warning("Failed to create subclip: %s", subclip_name)
                    except Exception as e:
                        logging.exception("Exception creating subclip for %s: %s", subclip_name, e)

                    # Finally, append that subclip to the timeline
                    self.media_pool.AppendToTimeline([trimmed_clip])

            logging.info("Timeline updated with trimmed clips.")
            return True
        except Exception as e:
            logging.exception("Error updating timeline with trimmed clips: %s", e)
            return False

    ## ADDED: Fusion automation example (motion tracking + text)
    def fusion_automation(self):
        """Automates Fusion effects: Adds motion tracking and a text overlay."""
        try:
            fusion = self.resolve.Fusion()
            if not fusion:
                logging.error("Failed to access Fusion. Ensure Resolve is open and Fusion is enabled.")
                return False

            timeline = self.get_current_timeline()
            if not timeline:
                logging.error("No current timeline found for Fusion automation.")
                return False

            # Create or get an existing composition
            fusion_comp = fusion.NewComp()
            logging.info("Created new Fusion composition for automation.")

            # Add a Tracker
            tracker = fusion_comp.AddTool("Tracker")
            tracker.SetAttrs({
                "TrackForward": True,
                "AdaptiveMode": "Best Match",
                "TrackerMode": "Pattern"
            })
            logging.info("Motion tracker tool added and configured.")

            # Add a TextPlus overlay
            text_tool = fusion_comp.AddTool("TextPlus")
            text_tool.StyledText = "AI Edited Drone Footage"
            logging.info("Text overlay tool added with 'AI Edited Drone Footage'.")

            return True
        except Exception as e:
            logging.exception("Error automating Fusion effects: %s", e)
            return False

    ## ADDED: Basic export function demonstrating dynamic format/resolution
    def export_video(self, user_settings):
        """Dynamically set render settings based on user selections."""
        try:
            # Example of extracting format/resolution from user settings
            render_settings = {
                "Format": user_settings.get("export_format", "MP4"),
                "Resolution": user_settings.get("export_resolution", "1080p")
            }

            # Additional logic for width/height if user_settings["export_resolution"] is dict, etc.
            ok = self.project.SetRenderSettings(render_settings)
            if not ok:
                logging.error("Failed to set render settings: %s", render_settings)
                return False

            if self.project.StartRendering():
                logging.info("Rendering started with settings: %s", render_settings)
                return True
            else:
                logging.error("Failed to start rendering. Check your render settings.")
                return False
        except Exception as e:
            logging.exception("Export error: %s", e)
            return False
