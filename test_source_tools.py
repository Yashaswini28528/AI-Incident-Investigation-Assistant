import source_tools


def test_prevents_access_outside_source_directory(
    tmp_path,
    monkeypatch
):

    # Create a temporary permitted source directory
    source_root = tmp_path / "source_code"
    source_root.mkdir()

    monkeypatch.setattr(
        source_tools,
        "SOURCE_ROOT",
        source_root
    )

    # Attempt to access a file outside the permitted directory
    result = source_tools.read_source_code.invoke({
        "relative_path": "../../.env"
    })

    assert result == (
        "Access denied: file must be inside the source_code folder."
    )
def test_rejects_unsupported_file_extension(
    tmp_path,
    monkeypatch
):

    source_root = tmp_path / "source_code"
    source_root.mkdir()

    # Create a file that should not be readable
    secret_file = source_root / "secrets.env"
    secret_file.write_text(
        "GROQ_API_KEY=example",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        source_tools,
        "SOURCE_ROOT",
        source_root
    )

    result = source_tools.read_source_code.invoke({
        "relative_path": "secrets.env"
    })

    assert result == "Unsupported file type."

def test_rejects_oversized_source_file(
    tmp_path,
    monkeypatch
):

    source_root = tmp_path / "source_code"
    source_root.mkdir()

    # Create a source file larger than 100 KB
    large_file = source_root / "large_file.py"
    large_file.write_text(
        "A" * 100_001,
        encoding="utf-8"
    )

    monkeypatch.setattr(
        source_tools,
        "SOURCE_ROOT",
        source_root
    )

    result = source_tools.read_source_code.invoke({
        "relative_path": "large_file.py"
    })

    assert result == (
        "File is too large. Maximum allowed size is 100 KB."
    )
def test_handles_invalid_utf8_source_file(
    tmp_path,
    monkeypatch
):

    source_root = tmp_path / "source_code"
    source_root.mkdir()

    invalid_file = source_root / "invalid.py"
    invalid_file.write_bytes(b"\xff\xfe\xfa")

    monkeypatch.setattr(
        source_tools,
        "SOURCE_ROOT",
        source_root
    )

    result = source_tools.read_source_code.invoke({
        "relative_path": "invalid.py"
    })

    assert result == (
        "Unable to read file: UTF-8 encoding is required."
    )
    