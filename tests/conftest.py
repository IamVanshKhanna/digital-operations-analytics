import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from data.generate_all import generate_all


@pytest.fixture(scope="session")
def data():
    return generate_all()


@pytest.fixture(scope="session")
def config(data):
    return data['config']
