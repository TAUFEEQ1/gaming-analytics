# Warehouse Luigi Pipeline

A Luigi-based data pipeline for warehouse operations.

## Structure

```env
warehouse/
├── __init__.py
├── run.py              # Main entry point
├── README.md
├── config/
│   └── luigi.cfg       # Luigi configuration
├── tasks/
│   ├── __init__.py
│   └── example_task.py # Luigi task definitions
└── data/               # Output directory for pipeline data
```

## Usage

Run the pipeline:

```bash
python warehouse/run.py
```

Or with Luigi configuration:

```bash
LUIGI_CONFIG_PATH=warehouse/config/luigi.cfg python warehouse/run.py
```

Run with central scheduler:

```bash
luigid --port 8082  # Start scheduler in one terminal
python warehouse/run.py  # Run pipeline in another terminal
```

## Creating New Tasks

1. Create a new task file in `tasks/` directory
2. Define Luigi tasks by inheriting from `luigi.Task`
3. Implement `requires()`, `output()`, and `run()` methods
4. Import and use in `run.py`
