from pydantic import BaseModel
from typing import Type, Any, get_args, get_origin
from types import MappingProxyType


def fix_extra_forbid(model_cls: Type[BaseModel]) -> Type[BaseModel]:
    """
    Recursively copy the pydantic model class and nested pydantic models,
    changing any config.extra == 'forbid' to 'ignore'.
    """

    # Helper to check if a type is a subclass of BaseModel
    def is_pydantic_model(t: Any) -> bool:
        try:
            return issubclass(t, BaseModel)
        except TypeError:
            return False

    # Fix model_config by replacing extra='forbid' -> extra='ignore'
    def fix_config(orig_config: MappingProxyType) -> MappingProxyType:
        config_dict = dict(orig_config)
        if config_dict.get("extra") == "forbid":
            config_dict["extra"] = "ignore"
        return MappingProxyType(config_dict)

    # Recursively fix nested models inside annotations
    def fix_field_type(field_type: Any) -> Any:
        origin = get_origin(field_type)
        args = get_args(field_type)

        # If field_type is a pydantic model, fix it recursively
        if is_pydantic_model(field_type):
            return fix_extra_forbid(field_type)

        # If it's a generic container like List[Model], Optional[Model], etc
        if origin and args:
            fixed_args = tuple(fix_field_type(arg) for arg in args)
            try:
                return origin[fixed_args]
            except TypeError:
                # Sometimes origin is not subscriptable, fallback:
                return field_type

        # Otherwise return as is
        return field_type

    # Create new namespace dict for the new model class
    namespace = {}

    # Fix config if needed
    orig_config = getattr(model_cls, "model_config", None)
    if orig_config is not None:
        namespace["model_config"] = fix_config(orig_config)

    # Fix fields annotations recursively
    annotations = getattr(model_cls, "__annotations__", {})
    fixed_annotations = {}
    for field_name, field_type in annotations.items():
        fixed_annotations[field_name] = fix_field_type(field_type)

    namespace["__annotations__"] = fixed_annotations

    # Copy class attributes except model_config and annotations (which we handled)
    for attr_name, attr_value in model_cls.__dict__.items():
        if attr_name not in ("model_config", "__annotations__", "__dict__", "__weakref__", "__module__"):
            namespace[attr_name] = attr_value

    # Create new class with same name + suffix to avoid confusion (optional)
    new_name = model_cls.__name__ + "Fixed"

    new_model = type(new_name, (BaseModel,), namespace)

    return new_model
