class VideoPublishError(Exception):
    def __init__(self, errors: dict[str, list[str]]):
        self.errors = errors
        super().__init__("Failed to publish video")

class VideoNotFound(Exception):
    pass

class VideoArchiveFailed(Exception):
    pass

class DuplicateEntryError(Exception):
    pass


# Thumbnail upload
class NoImageInRequest(Exception):
    pass

class ThumbnailAlreadyExists(Exception):
    pass

