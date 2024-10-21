from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class SyncRequest(_message.Message):
    __slots__ = ("client_id", "last_change")
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    LAST_CHANGE_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    last_change: int
    def __init__(self, client_id: _Optional[str] = ..., last_change: _Optional[int] = ...) -> None: ...

class Change(_message.Message):
    __slots__ = ("client_id", "operation", "last_change", "content", "position")
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    LAST_CHANGE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    operation: str
    last_change: int
    content: str
    position: int
    def __init__(self, client_id: _Optional[str] = ..., operation: _Optional[str] = ..., last_change: _Optional[int] = ..., content: _Optional[str] = ..., position: _Optional[int] = ...) -> None: ...

class Ack(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...
