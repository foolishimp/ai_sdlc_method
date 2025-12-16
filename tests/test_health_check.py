import requests
import subprocess
import time
import pytest

# Define the address for our test server
HOST = "localhost"
PORT = 8888
BASE_URL = f"http://{HOST}:{PORT}"

@pytest.fixture(scope="module")
def server():
    """Fixture to start and stop the health check server."""
    # Start the server as a background process
    server_process = subprocess.Popen(
        ["python", "src/health_server.py", "--port", str(PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait a moment for the server to start
    time.sleep(1)
    
    # Yield control to the tests
    yield
    
    # Teardown: stop the server
    server_process.terminate()
    server_process.wait()

def test_health_check_endpoint_returns_200(server):
    """
    Given the health server is running
    When a GET request is made to the /health endpoint
    Then the response status code should be 200
    """
    # Validates: REQ-F-HEALTH-001
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    except requests.exceptions.ConnectionError as e:
        pytest.fail(f"Failed to connect to the server: {e}")

