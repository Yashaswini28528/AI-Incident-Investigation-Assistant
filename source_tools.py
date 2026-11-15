
from pathlib import Path
from langchain_core.tools import tool


# 1. Define the only folder the tool is allowed to access
SOURCE_ROOT = (
    Path(__file__).resolve().parent / "source_code"
)


# 2. Create the LangChain tool
@tool
def read_source_code(relative_path: str) -> str:
    """
    Read an application source-code file from the source_code folder.

    Provide a relative path such as app/database.py.
    Only supported source-code files inside source_code can be read.
    """

    # Resolve the requested file path
    file_path = (SOURCE_ROOT / relative_path).resolve()

    # 3. Prevent access outside the permitted folder
    if not file_path.is_relative_to(SOURCE_ROOT.resolve()):
        return "Access denied: file must be inside the source_code folder."

    # 4. Allow only supported source-code extensions
    allowed_extensions = {
        ".py", ".java", ".js", ".ts",
        ".jsx", ".tsx", ".cs"
    }

    if file_path.suffix.lower() not in allowed_extensions:
        return "Unsupported file type."

    # 5. Check whether the requested file exists
    if not file_path.is_file():
        return "File not found in the source_code folder."

    # 6. Prevent reading excessively large files
    if file_path.stat().st_size > 100_000:
        return "File is too large. Maximum allowed size is 100 KB."

    # 7. Read the source code
    try:
        source_content = file_path.read_text(encoding="utf-8")
        return source_content

    except UnicodeDecodeError:
        return "Unable to read file: UTF-8 encoding is required."
