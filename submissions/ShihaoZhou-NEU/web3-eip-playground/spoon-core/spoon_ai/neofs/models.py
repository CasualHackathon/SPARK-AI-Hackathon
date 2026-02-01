"""Pydantic models describing NeoFS REST API payloads."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Target(BaseModel):
    role: str
    keys: List[str] = Field(default_factory=list)


class Filter(BaseModel):
    header_type: str = Field(alias='headerType')
    match_type: str = Field(alias='matchType')
    key: str
    value: str


class Record(BaseModel):
    action: str
    operation: str
    filters: List[Filter] = Field(default_factory=list)
    targets: List[Target] = Field(default_factory=list)


class Rule(BaseModel):
    verb: str
    container_id: str = Field(alias='containerId')


class Bearer(BaseModel):
    name: str
    object: Optional[List[Record]] = None
    container: Optional[Rule] = None


class TokenResponse(BaseModel):
    name: str
    type: str
    token: str


class BinaryBearer(BaseModel):
    token: str


class Attribute(BaseModel):
    key: str
    value: str


class ContainerPostInfo(BaseModel):
    container_name: str = Field(alias='containerName')
    placement_policy: str = Field(alias='placementPolicy')
    basic_acl: str = Field(alias='basicAcl')
    attributes: List[Attribute] = Field(default_factory=list)


class ContainerInfo(BaseModel):
    container_id: str = Field(alias='containerId')
    container_name: str = Field(alias='containerName')
    version: str
    owner_id: str = Field(alias='ownerId')
    basic_acl: str = Field(alias='basicAcl')
    canned_acl: str = Field(alias='cannedAcl')
    placement_policy: str = Field(alias='placementPolicy')
    attributes: List[Attribute] = Field(default_factory=list)


class ContainerList(BaseModel):
    size: int
    containers: List[ContainerInfo]


class Eacl(BaseModel):
    container_id: str = Field(alias='containerId')
    records: List[Record]


class SearchFilter(BaseModel):
    key: str
    value: str
    match: str


class SearchRequest(BaseModel):
    filters: List[SearchFilter]
    attributes: Optional[List[str]] = None


class Address(BaseModel):
    container_id: str = Field(alias='containerId')
    object_id: str = Field(alias='objectId')


class ObjectBaseInfo(BaseModel):
    address: Address
    name: str
    file_path: str = Field(alias='filePath')


class ObjectList(BaseModel):
    size: int
    objects: List[ObjectBaseInfo]


class ObjectBaseInfoV2(BaseModel):
    object_id: str = Field(alias='objectId')
    attributes: Dict[str, Any]


class ObjectListV2(BaseModel):
    objects: List[ObjectBaseInfoV2]
    cursor: str


class Balance(BaseModel):
    address: str
    value: str
    precision: int


class NetworkInfo(BaseModel):
    """Describes network configuration fees reported by the gateway."""
    audit_fee: int = Field(alias='auditFee')
    container_fee: int = Field(alias='containerFee')
    epoch_duration: int = Field(alias='epochDuration')
    homomorphic_hashing_disabled: bool = Field(alias='homomorphicHashingDisabled')
    max_object_size: int = Field(alias='maxObjectSize')
    named_container_fee: int = Field(alias='namedContainerFee')
    storage_price: int = Field(alias='storagePrice')
    withdrawal_fee: int = Field(alias='withdrawalFee')


class SuccessResponse(BaseModel):
    success: bool

class UploadAddress(BaseModel):
    container_id: str = Field(alias='container_id')
    object_id: str = Field(alias='object_id')

class ErrorResponse(BaseModel):
    message: str
    type: str
    code: Optional[int] = None
