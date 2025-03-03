import os
import shutil
import tempfile
import unittest


class TestTempDir(unittest.TestCase):
    def test_temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        # print(f"Temporary directory: {temp_dir}")
        # print(f"Current working directory: {os.getcwd()}")
        sub_dir = os.path.join(temp_dir, "subdir")
        os.makedirs(sub_dir)
        file_path = os.path.join(sub_dir, "test_file.txt")
        with open(file_path, "w") as f:
            f.write("test content")
        # print(f"Contents of sub_dir: {os.listdir(sub_dir)}")
        self.assertTrue(os.path.exists(sub_dir))
        self.assertTrue(os.path.exists(file_path))
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
