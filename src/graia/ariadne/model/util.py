from typing import TYPE_CHECKING, Literal, Union

from pydantic import BaseConfig, BaseModel, Extra
from typing_extensions import NotRequired, TypedDict

if TYPE_CHECKING:
    from ..typing import AbstractSetIntStr, DictStrAny, MappingIntStrAny


class AriadneBaseModel(BaseModel):
    """
    Ariadne 一切数据模型的基类.
    """

    def dict(
        self,
        *,
        include: Union[None, "AbstractSetIntStr", "MappingIntStrAny"] = None,
        exclude: Union[None, "AbstractSetIntStr", "MappingIntStrAny"] = None,
        by_alias: bool = False,
        skip_defaults: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> "DictStrAny":
        _, *_ = by_alias, exclude_none, skip_defaults
        return super().dict(
            include=include,  # type: ignore
            exclude=exclude,  # type: ignore
            by_alias=True,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=True,
        )

    class Config(BaseConfig):
        """Ariadne BaseModel 设置"""

        extra = Extra.allow
        arbitrary_types_allowed = True


class AriadneOptions(TypedDict):
    installed_log: NotRequired[Literal[True]]
    inject_bypass_listener: NotRequired[Literal[True]]
    default_account: NotRequired[int]
