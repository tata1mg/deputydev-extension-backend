from enum import Enum


class LanguageIdentifiers(Enum):
    FUNCTION_DEFINITION = "function_definition"
    CLASS_DEFINITION = "class_definition"
    FUNCTION_IDENTIFIER = "function_identifier"
    CLASS_IDENTIFIER = "class_identifier"
    DECORATOR = "decorator"
    FUNCTION_CLASS_WRAPPER = "function_class_wrapper"
    NAMESPACE = "namespace"
    DECORATED_DEFINITION = "decorated_definition"
    NAMESPACE_IDENTIFIER = "namespace_identifier"


js_family_identifiers = {
    LanguageIdentifiers.FUNCTION_DEFINITION.value: [
        "method_definition",
        "function_declaration",
        "generator_function_declaration",
    ],
    LanguageIdentifiers.CLASS_DEFINITION.value: ["class_declaration", "abstract_class_declaration"],
    LanguageIdentifiers.FUNCTION_IDENTIFIER.value: ["property_identifier", "identifier"],
    LanguageIdentifiers.CLASS_IDENTIFIER.value: ["type_identifier"],
    LanguageIdentifiers.DECORATOR.value: "NA",
    LanguageIdentifiers.FUNCTION_CLASS_WRAPPER.value: ["expression_statement"],
    LanguageIdentifiers.NAMESPACE.value: ["namespace", "internal_module"],
    LanguageIdentifiers.NAMESPACE_IDENTIFIER.value: ["identifier"],
    LanguageIdentifiers.DECORATED_DEFINITION.value: [],
}

java_family_identifiers = {
    LanguageIdentifiers.FUNCTION_DEFINITION.value: [
        "method_declaration",
        "function_declaration",
        "constructor_declaration",
        "lambda_expression",
        "annotation_type_declaration",
    ],
    LanguageIdentifiers.CLASS_DEFINITION.value: [
        "class_declaration",
        "abstract_class_declaration",
        "interface_declaration",
        "enum_declaration",
    ],
    LanguageIdentifiers.FUNCTION_IDENTIFIER.value: ["identifier"],
    LanguageIdentifiers.CLASS_IDENTIFIER.value: ["identifier"],
    LanguageIdentifiers.DECORATOR.value: "NA",
    LanguageIdentifiers.FUNCTION_CLASS_WRAPPER.value: [],
    LanguageIdentifiers.NAMESPACE.value: ["NA"],
    LanguageIdentifiers.NAMESPACE_IDENTIFIER.value: [],
}
ruby_family_identifiers = {
    LanguageIdentifiers.FUNCTION_DEFINITION.value: ["method", "singleton_method", "class_method"],
    LanguageIdentifiers.CLASS_DEFINITION.value: ["class", "singleton_class"],
    LanguageIdentifiers.FUNCTION_IDENTIFIER.value: ["identifier", "constant"],
    LanguageIdentifiers.CLASS_IDENTIFIER.value: ["constant"],
    LanguageIdentifiers.DECORATOR.value: "NA",
    LanguageIdentifiers.FUNCTION_CLASS_WRAPPER.value: [],
    LanguageIdentifiers.NAMESPACE.value: ["module"],
    LanguageIdentifiers.NAMESPACE_IDENTIFIER.value: ["constant"],
}

kotlin_family_identifiers = {
    LanguageIdentifiers.FUNCTION_DEFINITION.value: [
        "function_declaration",
        "lambda_expression",
        "anonymous_function",
        "constructor_declaration",
    ],
    LanguageIdentifiers.CLASS_DEFINITION.value: ["class_declaration", "object_declaration", "interface_declaration"],
    LanguageIdentifiers.FUNCTION_IDENTIFIER.value: ["simple_identifier"],
    LanguageIdentifiers.CLASS_IDENTIFIER.value: ["type_identifier"],
    LanguageIdentifiers.DECORATOR.value: "NA",
    LanguageIdentifiers.FUNCTION_CLASS_WRAPPER.value: [],
    LanguageIdentifiers.NAMESPACE.value: [],
    LanguageIdentifiers.NAMESPACE_IDENTIFIER.value: [],
}

python_family_identifiers = {
    LanguageIdentifiers.FUNCTION_DEFINITION.value: ["function_definition"],
    LanguageIdentifiers.DECORATED_DEFINITION.value: ["decorated_definition"],
    LanguageIdentifiers.CLASS_DEFINITION.value: ["class_definition"],
    LanguageIdentifiers.FUNCTION_IDENTIFIER.value: ["identifier"],
    LanguageIdentifiers.CLASS_IDENTIFIER.value: ["identifier"],
    LanguageIdentifiers.DECORATOR.value: "decorator",
    LanguageIdentifiers.FUNCTION_CLASS_WRAPPER.value: ["decorated_definition"],
    LanguageIdentifiers.NAMESPACE.value: ["NA"],
    LanguageIdentifiers.NAMESPACE_IDENTIFIER.value: [],
}

chunk_language_identifiers = {
    "python": python_family_identifiers,
    "javascript": js_family_identifiers,
    "tsx": js_family_identifiers,
    "typescript": js_family_identifiers,
    "java": java_family_identifiers,
    "ruby": ruby_family_identifiers,
    "kotlin": kotlin_family_identifiers,
}
