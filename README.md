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
├── populate_test_data.py   # Generates a mixed Fedora test dataset
├── populate_is_member_of.py # Generates an inbound-membership test dataset
├── utils/                  # Utility modules
│   └── statistics_tracker.py  # Statistics collection and reporting
│   └── stats_analyzer.py      # Compares saved Locust workflow results
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

1. **Create atomic and Archival Group collections** - Each simulated user creates one of each in transactions, with external-content metadata children. The workflow records transaction commit time, total duration, and OCFL filesystem growth.
2. **PATCH atomic collection** (weight: 10) - Repeatedly updates a counter property and records request duration and OCFL growth.
3. **PATCH Archival Group collection** (weight: 10) - Performs the equivalent updates on the Archival Group collection for comparison.
4. **GET Root** (weight: 3) - Fetches the repository root.
5. **GET Container** (weight: 2) - Fetches `/container`.
6. **Create Resource** (weight: 1) - Creates a simple resource via POST.

Task weights determine the relative frequency of execution.

## Supporting Scripts

### `populate_test_data.py`

Populates Fedora with a configurable mixed workload for broader repository testing. It creates an approximately even mix of atomic resources and Archival Groups, each with a randomized number of children, including binaries. It also introduces randomized RDF types, child-to-child links, metadata updates, deletions, and occasional tombstone purges. With `--setup-containers`, it first creates five DirectContainers containing 0, 1, 10, 100, and 1,000 children, including random deletions.

This script is standalone; it requires only a reachable configured Fedora instance and does not depend on another project script having run first.

```bash
python populate_test_data.py --num-resources 10000 --workers 10
python populate_test_data.py --num-resources 10000 --setup-containers
```

### `populate_is_member_of.py`

Creates one parent resource and 10,000 child resources that point to it with `pcdm:memberOf`. It is intended to populate an inbound-reference listing workload, rather than measure request timings directly. The member resources are created concurrently using 10 workers.

This script is standalone and does not depend on `populate_test_data.py`; it adds its own parent and member resources. Its dataset size and concurrency are currently configured by the `NUM_MEMBERS` and `NUM_WORKERS` constants in the script.

```bash
python populate_is_member_of.py
```

### `utils/stats_analyzer.py`

Analyzes the latest saved custom statistics file from a Locust run. It compares atomic and Archival Group collection creation and PATCH workflows, reporting average request/workflow durations, OCFL file/directory/size deltas, and estimated storage growth per PATCH update.

It depends on `locustfile.py` having completed at least one run that wrote statistics under `results/<TEST_CONFIG_NAME>/`. Pass a configuration name to analyze a specific results subdirectory; without one, it uses `TEST_CONFIG_NAME` or `default`.

```bash
python utils/stats_analyzer.py
python utils/stats_analyzer.py autoversioning
```

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
