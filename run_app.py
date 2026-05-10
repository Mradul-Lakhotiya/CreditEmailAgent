import os
import sys

# Set pure python implementation for protobuf to fix Python 3.14 incompatibility
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from streamlit.web import cli

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(cli.main())
