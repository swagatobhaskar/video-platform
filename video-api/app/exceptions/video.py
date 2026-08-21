class VideoPublishError(Exception):
    pass

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

