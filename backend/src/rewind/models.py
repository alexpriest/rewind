from pydantic import BaseModel


class PhotoResponse(BaseModel):
    id: int
    identifier: str
    file_type: str | None
    has_thumbnail: bool


class EntryResponse(BaseModel):
    uuid: str
    creation_date: str
    text: str | None
    snippet: str | None
    starred: bool
    latitude: float | None
    longitude: float | None
    place_name: str | None
    locality: str | None
    admin_area: str | None
    country: str | None
    weather_description: str | None
    weather_temp_c: float | None
    word_count: int | None
    tags: list[str]
    photos: list[PhotoResponse]


class TagResponse(BaseModel):
    id: int
    name: str
    tag_type: str
    ai_suggested_type: str | None
    user_confirmed: bool
    entry_count: int


class EntryListResponse(BaseModel):
    entries: list[EntryResponse]
    total: int
    page: int
    page_size: int


class ImportStatus(BaseModel):
    id: str
    status: str
    progress: float
    message: str
    entry_count: int | None = None
    tag_count: int | None = None
    photo_count: int | None = None


class TagClassifyRequest(BaseModel):
    tag_ids: list[int]


class TagUpdateRequest(BaseModel):
    tag_type: str


class BulkConfirmRequest(BaseModel):
    tag_ids: list[int]


class TimelineGroup(BaseModel):
    month: str
    label: str
    entries: list[EntryResponse]
    count: int


class TimelineResponse(BaseModel):
    groups: list[TimelineGroup]
    total: int


class PlaceCount(BaseModel):
    name: str
    count: int


class MapPointResponse(BaseModel):
    uuid: str
    latitude: float
    longitude: float
    creation_date: str
    snippet: str | None
    place_name: str | None
    photo_id: int | None


class ReportGenerateRequest(BaseModel):
    person_tag_id: int
    date_from: str | None = None
    date_to: str | None = None


class ReportStatusResponse(BaseModel):
    id: str
    status: str  # 'generating' | 'done' | 'error'
    progress: float
    message: str
    person_name: str | None = None


class GraphNodeResponse(BaseModel):
    node_type: str
    node_id: str
    label: str
    entry_count: int
    first_date: str | None
    last_date: str | None


class GraphEdgeResponse(BaseModel):
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    weight: int
    first_date: str | None
    last_date: str | None


class GraphResponse(BaseModel):
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
