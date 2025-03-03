import logging
import os
import platform

class ResolveAPIHelper:
    """Helper class to manage DaVinci Resolve API version compatibility."""
    
    def __init__(self, resolve):
        self.resolve = resolve
        self.api_version = self._get_api_version()
        logging.info(f"DaVinci Resolve API Version: {self.api_version}")
        self.available_methods = self._detect_available_methods()
        
    def _get_api_version(self):
        """Attempt to get the Resolve API version."""
        try:
            if hasattr(self.resolve, "GetVersionString") and callable(self.resolve.GetVersionString):
                return self.resolve.GetVersionString()
            else:
                # Try alternative methods to determine version
                project_manager = self.resolve.GetProjectManager()
                if project_manager:
                    project = project_manager.GetCurrentProject()
                    if project:
                        # Different versions expose different methods
                        for method in ["GetSetting", "GetPresetList", "GetRenderFormats"]:
                            if hasattr(project, method):
                                return f"Unknown (has {method})"
                return "Unknown"
        except Exception as e:
            logging.warning(f"Failed to determine API version: {e}")
            return "Unknown"
    
    def _detect_available_methods(self):
        """Detect available methods in the current Resolve API version."""
        available = {}
        
        # Get current project and timeline
        try:
            project_manager = self.resolve.GetProjectManager()
            project = project_manager.GetCurrentProject()
            timeline = project.GetCurrentTimeline() if project else None
            media_pool = project.GetMediaPool() if project else None
            
            # Check Timeline methods
            if timeline:
                available["timeline.AddTransition"] = hasattr(timeline, "AddTransition") and callable(timeline.AddTransition)
                available["timeline.RemoveItem"] = hasattr(timeline, "RemoveItem") and callable(timeline.RemoveItem)
                available["timeline.GetItemListInTrack"] = hasattr(timeline, "GetItemListInTrack") and callable(timeline.GetItemListInTrack)
                available["timeline.InsertFusionTitleIntoTimeline"] = hasattr(timeline, "InsertFusionTitleIntoTimeline") and callable(timeline.InsertFusionTitleIntoTimeline)
                available["timeline.InsertFusionGeneratorIntoTimeline"] = hasattr(timeline, "InsertFusionGeneratorIntoTimeline") and callable(timeline.InsertFusionGeneratorIntoTimeline)
                available["timeline.CreateSubtitlesFromAudio"] = hasattr(timeline, "CreateSubtitlesFromAudio") and callable(timeline.CreateSubtitlesFromAudio)
                
            # Check MediaPool methods
            if media_pool:
                available["mediaPool.DuplicateMediaPoolItem"] = hasattr(media_pool, "DuplicateMediaPoolItem") and callable(media_pool.DuplicateMediaPoolItem)
                available["mediaPool.AppendToTimeline"] = hasattr(media_pool, "AppendToTimeline") and callable(media_pool.AppendToTimeline)
                available["mediaPool.TranscribeAudio"] = hasattr(media_pool, "TranscribeAudio") and callable(media_pool.TranscribeAudio)
                
            # Log availability
            for method, available_status in available.items():
                logging.info(f"API Method {method}: {'Available' if available_status else 'Not Available'}")
                
        except Exception as e:
            logging.warning(f"Error detecting available methods: {e}")
            
        return available
    
    def is_method_available(self, method_name):
        """Check if a specific method is available in the current API version."""
        return self.available_methods.get(method_name, False)
    
    def safe_add_transition(self, timeline, transition_type, clip1, clip2, duration=30):
        """Safely add a transition between clips if the API supports it."""
        if self.is_method_available("timeline.AddTransition"):
            try:
                result = timeline.AddTransition(transition_type, clip1, clip2, duration)
                if result:
                    logging.info(f"Successfully added {transition_type} transition")
                else:
                    logging.warning(f"Failed to add {transition_type} transition")
                return result
            except Exception as e:
                logging.exception(f"Error adding transition: {e}")
                return False
        else:
            logging.info("Skipping transition - AddTransition method not available in this API version")
            return False
    
    def safe_remove_timeline_item(self, timeline, item):
        """Safely remove an item from timeline if the API supports it."""
        if self.is_method_available("timeline.RemoveItem"):
            try:
                result = timeline.RemoveItem(item)
                return result
            except Exception as e:
                logging.exception(f"Error removing timeline item: {e}")
                return False
        else:
            logging.info("Skipping item removal - RemoveItem method not available in this API version")
            return False
            
    def get_feature_support_info(self):
        """Return a human-readable summary of API feature support."""
        support_info = {
            "Transitions": self.is_method_available("timeline.AddTransition"),
            "Timeline Item Removal": self.is_method_available("timeline.RemoveItem"),
            "Fusion Titles": self.is_method_available("timeline.InsertFusionTitleIntoTimeline"),
            "Fusion Generators": self.is_method_available("timeline.InsertFusionGeneratorIntoTimeline"),
            "Subtitles from Audio": self.is_method_available("timeline.CreateSubtitlesFromAudio"),
            "Media Duplication": self.is_method_available("mediaPool.DuplicateMediaPoolItem"),
            "Timeline Appending": self.is_method_available("mediaPool.AppendToTimeline"),
            "Audio Transcription": self.is_method_available("mediaPool.TranscribeAudio")
        }
        
        return support_info