# Fcrepo Performance Testing Suite

A Python-based performance testing suite for Fedora Repository (fcrepo) using Locust. This project measures response performance and tracks statistics about file counts and sizes during continuous request testing.

## Requirements

- Python >= 3.9
- virtualenv
- Fedora Repository instance (fcrepo)

## Project Structure

```
.
├── locustfile.py           # Main Locust test scenarios
├── utils/                  # Utility modules
│   └── statistics_tracker.py  # Statistics collection and reporting
├── tests/                  # Additional test scripts
├── results/                # Test results and statistics (git-ignored)
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment configuration
└── README.md              # This file
```

## Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and configure it for your fcrepo instance:

```bash
cp .env.example .env
```

Edit `.env` with your fcrepo settings:
```bash
FCREPO_HOST=http://localhost:8080
FCREPO_BASE_PATH=/fcrepo/rest
```

## Running Tests

### Basic Usage

Run Locust with the web UI:

```bash
locust
```

Then open your browser to http://localhost:8089 to configure and start the test.

### Headless Mode

Run without the web UI:

```bash
locust --users 10 \
       --spawn-rate 1 \
       --run-time 5m \
       --headless
```

### Command Line Options

- `--users`: Number of concurrent users to simulate
- `--spawn-rate`: Rate to spawn users (users per second)
- `--run-time`: Test duration (e.g., 10m, 1h, 300s)
- `--headless`: Run without web UI
- `--html`: Generate HTML report (e.g., `--html=results/report.html`)

**Note:** The fcrepo host and base path are configured in the `.env` file, not via command line parameters.

## Test Scenarios

The current test suite includes:

1. **GET Root** (weight: 3) - Fetches the repository root
2. **GET Container** (weight: 2) - Fetches a container resource
3. **Create Resource** (weight: 1) - Creates new resources via POST

Task weights determine the relative frequency of execution.

## Statistics Collection

The `StatisticsTracker` utility automatically collects:

- Response times
- Status codes
- Content sizes
- Resource creation counts
- Timestamps for all operations

Statistics are saved to the `results/` directory in JSON format.

## Deactivating Environment

When you're done:

```bash
deactivate
```

## Development

### Adding New Test Scenarios

Edit `locustfile.py` and add new `@task` methods to the `FcrepoUser` class:

```python
@task(weight)
def my_test(self):
    response = self.client.get("/path/to/resource")
    # Handle response...
```

### Customizing Statistics

Modify `utils/statistics_tracker.py` to add additional metrics or change how data is collected and saved.

## Results

Test results are stored in the `results/` directory and include:
- Locust's built-in statistics (HTML reports, CSV exports)
- Custom JSON statistics with detailed request/response information
- File count and size tracking over time