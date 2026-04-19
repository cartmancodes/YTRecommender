from dataclasses import dataclass


@dataclass
class VideoRef:
    id: str
    url: str
    title: str


@dataclass
class VideoMetadata:
    id: str
    url: str
    title: str
    channel: str
    duration: int
    views: int
    likes: int
    dislikes: int
    dislikes_available: bool


@dataclass
class ScoredVideo:
    metadata: VideoMetadata
    score: float
