import pytest
import os
from cnap.core import filedb

# Test the abstract class FileDatabase
class ConcreteFileDatabaseForTesting(filedb.FileDatabase):
    def __init__(self):
        pass

    def get_file(self, filename: str) -> str:
        return filename

def test_file_database_init():
    """Tests the initialization of the FileDatabase abstract class.

    Args:
        None

    Returns:
        None
    """
    db = ConcreteFileDatabaseForTesting()
    assert db is not None

def test_file_database_get_file():
    """Tests the get_file method of the FileDatabase abstract class.

    This test should be expanded based on the expected behavior of the get_file method.

    Args:
        None

    Returns:
        None
    """
    db = ConcreteFileDatabaseForTesting()
    assert db.get_file('file_id') == 'file_id'

# Test the concrete class LocalFileDatabase
def test_local_file_database_init(tmp_path):
    """Tests the initialization of the LocalFileDatabase class.

    Args:
        tmp_path (LocalPath): Temporary path provided by pytest's tmp_path fixture.

    Returns:
        None
    """
    root_dir = str(tmp_path)
    db = filedb.LocalFileDatabase(root_dir)
    assert db._root_dir == os.path.abspath(root_dir)

def test_local_file_database_get_file(tmp_path):
    """Tests the get_file method of the LocalFileDatabase class.

    This test checks if the get_file method correctly finds the given file and returns its local path.

    Args:
        tmp_path (LocalPath): Temporary path provided by pytest's tmp_path fixture.

    Returns:
        None
    """
    # Create a temporary file for testing
    filename = 'test_file.txt'
    file_path = tmp_path / filename
    file_path.write_text('Hello, world!')

    root_dir = str(tmp_path)
    db = filedb.LocalFileDatabase(root_dir)
    assert db.get_file(filename) == str(file_path)

def test_local_file_database_get_file_invalid_root():
    """Tests the get_file method of the LocalFileDatabase class with an invalid root directory.

    Args:
        None

    Returns:
        None
    """
    root_dir = '/invalid/path'
    db = filedb.LocalFileDatabase(root_dir)
    with pytest.raises(FileNotFoundError):
        db.get_file('filename')

def test_local_file_database_get_file_not_found(tmp_path):
    """Tests the get_file method of the LocalFileDatabase class with a file not found.

    Args:
        tmp_path (LocalPath): Temporary path provided by pytest's tmp_path fixture.

    Returns:
        None
    """
    root_dir = str(tmp_path)
    db = filedb.LocalFileDatabase(root_dir)
    with pytest.raises(FileNotFoundError):
        db.get_file('non_existent_file.txt')
