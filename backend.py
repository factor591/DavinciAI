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
                # ADDED: More explicit logging on why it failed
                logging.warning(
                    "Attempt %d: Exception connecting to DaVinci Resolve: %s",
                    attempt + 1, e
                )
                logging.warning("Check if fusionscript.dll is on PATH or bundled with your EXE.")  # ADDED
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
            if not hasattr(clip_item, "GetClipProperty"):
                logging.warning("Clip item of type %s lacks GetClipProperty.", type(clip_item))
                return "Unknown"

            name = (
                clip_item.GetClipProperty("File Path")
                or clip_item.GetClipProperty("Clip Name")
                or clip_item.GetClipProperty("Name")
            )
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
            timeline = self.get_current_timeline()
            if not timeline:
                logging.warning("Cannot update timeline: No current timeline found.")
                return False

            logging.info("Clearing original timeline clips.")
            remove_item_method = getattr(timeline, 'RemoveItem', None)
            if remove_item_method and callable(remove_item_method):
                all_clips = timeline.GetItemListInTrack("video", 1)
                for c in all_clips:
                    remove_item_method(c)
            else:
                logging.warning("timeline.RemoveItem is not available in this API version. Skipping old clip removal.")

            for (source_clip, start_sec, end_sec) in new_clips:
                clip_name = self.get_clip_name(source_clip)
                logging.info("Appending new clip: Original clip %s, from %s to %s", clip_name, start_sec, end_sec)

                can_duplicate = (
                    hasattr(self.media_pool, "DuplicateMediaPoolItem")
                    and callable(self.media_pool.DuplicateMediaPoolItem)
                )
                trimmed_clip = None
                if can_duplicate:
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

        add_transition_method = getattr(timeline, 'AddTransition', None)
        if add_transition_method and callable(add_transition_method):
            video_items = timeline.GetItemListInTrack("video", 1)
            for i in range(len(video_items) - 1):
                try:
                    transition_result = add_transition_method(
                        "Cross Dissolve", video_items[i], video_items[i+1], 30
                    )
                    if not transition_result:
                        logging.warning(
                            "Failed to add Cross Dissolve transition between clip %d and %d.",
                            i, i+1
                        )
                except Exception as e:
                    logging.exception(
                        "Exception adding transition between clip %d and %d: %s",
                        i, i+1, e
                    )
            logging.info("Attempted to add transitions between consecutive timeline clips.")
        else:
            logging.warning(
                "timeline.AddTransition is not available in this API version; skipping transitions."
            )
