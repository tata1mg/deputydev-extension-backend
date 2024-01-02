import inspect
import functools

# Global variable to store all functions decorated with @openaifunc
openai_functions = []

# Map python types to JSON schema types
type_mapping = {
    "int": "integer",
    "float": "number",
    "str": "string",
    "bool": "boolean",
    "list": "array",
    "tuple": "array",
    "dict": "object",
    "None": "null",
}


def get_type_mapping(param_type):
    param_type = param_type.replace("<class '", "")
    param_type = param_type.replace("'>", "")
    return type_mapping.get(param_type, "string")


def get_serialized_params(params, doc):
    response = {}
    for k, v in params.items():
        response.update({
            k: {
                "type": get_type_mapping(str(v.annotation)),
                "description": doc.split(f"{k}:")[1].split("\n")[0].strip(),
            }
        })
    return response


def openaifunc(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    # Get information about function parameters
    params = inspect.signature(func).parameters

    param_dict = get_serialized_params(params, inspect.cleandoc(func.__doc__ or ""))

    openai_functions.append(
        {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": inspect.cleandoc(func.__doc__ or ""),
                "parameters": {
                    "type": "object",
                    "properties": param_dict,
                    "required": list(param_dict.keys()),
                },
            },
        }
    )

    return wrapper


def get_openai_funcs():
    return openai_functions
