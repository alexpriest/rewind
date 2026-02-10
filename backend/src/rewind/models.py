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
