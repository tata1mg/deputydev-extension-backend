JAVASCRIPT_EXTENSIONS = {
    "js": "javascript",
    "jsx": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "es": "javascript",
    "es6": "javascript",
}

TYPESCRIPT_EXTENSIONS = {
    "ts": "typescript",
    "mts": "typescript",
    "cts": "typescript",
}

JAVA_EXTENSIONS = {"java": "java"}

TSX_EXTENSIONS = {"tsx": "tsx"}

EXTENSION_TO_LANGUAGE = {"py": "python", "html": "html", "kt": "kotlin", "go": "go", "json": "json"}

# We collect all the language dictionaries and create a single dict, making it easier to segregate as different extensions
# can be served from the same programming language
ALL_EXTENSIONS = {
    **JAVASCRIPT_EXTENSIONS,
    **TYPESCRIPT_EXTENSIONS,
    **JAVA_EXTENSIONS,
    **TSX_EXTENSIONS,
    **EXTENSION_TO_LANGUAGE,
}
