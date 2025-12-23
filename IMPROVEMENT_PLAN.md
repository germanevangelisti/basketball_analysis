# Basketball Video Analysis - Improvement Plan

This document outlines a comprehensive plan to improve the quality, performance, reliability, and feature set of the Basketball Video Analysis project.

## 1. Code Quality & Architecture

**Goal:** Make the codebase more maintainable, readable, and robust.

*   **Configuration Management**:
    *   **Current State**: Hardcoded values in `configs/configs.py`.
    *   **Improvement**: Migrate to `config.yaml` or `config.json`. Use a configuration loader (e.g., `hydra` or a custom class) to manage settings, environment variables, and model paths.
    *   **Benefit**: Easier to change settings without touching code; better support for different environments (local vs docker).

*   **Type Hinting & Static Analysis**:
    *   **Current State**: Few type hints; strict typing is missing.
    *   **Improvement**: Add Python type hints (`typing` module) to all function signatures. Set up `mypy` for static type checking.
    *   **Benefit**: catches bugs early; improves IDE autocompletion; acts as documentation.

*   **Logging**:
    *   **Current State**: Usage of `print()` statements for debugging and status.
    *   **Improvement**: Implement python's standard `logging` module. Configure different log levels (INFO, DEBUG, ERROR) and output formats (console, file).
    *   **Benefit**: Better observability; easier debugging in production/headless modes.

*   **Modularity**:
    *   **Current State**: `main.py` is quite linear and handles too many responsibilities (loading, tracking, assignment, drawing, saving).
    *   **Improvement**: Break down `main.py` into a `Pipeline` class. Isolate "Drawing" logic further from "Processing" logic.

## 2. Reliability & Testing

**Goal:** Ensure the system works as expected and prevent regressions.

*   **Unit Testing**:
    *   **Current State**: No visible tests.
    *   **Improvement**: Set up `pytest`. Write unit tests for utility functions (`bbox_utils.py`), math calculations (`SpeedAndDistanceCalculator`), and logic components (`BallAquisitionDetector`, `TeamAssigner`).
    *   **Target**: High test coverage for pure logic functions.

*   **Integration Testing**:
    *   **Improvement**: Create a small "smoke test" using a short (1-second) video clip or a mocked video reader to ensure the full pipeline runs without crashing.

*   **CI/CD**:
    *   **Improvement**: Add a GitHub Actions workflow to run `pytest` and `pylint`/`flake8` on every push.

## 3. Performance Optimization

**Goal:** Reduce processing time.

*   **Profiling**:
    *   **Action**: Run `cProfile` to identify bottlenecks.
    *   **Hypothesis**: YOLO inference and video writing are likely the slowest parts.

*   **Parallelization**:
    *   **Improvement**: If inference is done sequentially per frame (and not batched effectively), ensure batch processing is maximized.
    *   **Advanced**: Run detection, tracking, and processing in parallel processes (multiprocessing) where possible (e.g., separate thread for video reading/writing).

*   **Stub Management**:
    *   **Current State**: Pickle files are used for stubs.
    *   **Improvement**: Ensure stubs are versioned or validated against the video hash to prevent using stale data.

## 4. New Features

**Goal:** Expand capabilities.

*   **Pose Estimation (Future Work)**:
    *   **Proposal**: Integrate YOLOv8-pose or MediaPipe Pose.
    *   **Use Case**: Detect "Shooting" action, "Dribbling" mechanics, or rule violations (Traveling).

*   **User Interface (UI)**:
    *   **Proposal**: Build a web interface using **Streamlit** or **Gradio**.
    *   **Features**: Upload video, adjust confidence thresholds, view processing progress, download results/stats.

## 5. Documentation & Usability

**Goal:** Make the project easy to use for new developers and users.

*   **CLI Improvements**:
    *   **Improvement**: Use `argparse` (already there) or `click` / `typer` to expose more configuration options (e.g., `conf_threshold`, `model_weights`) directly from the command line.

*   **Developer Guide**:
    *   **Improvement**: Add a section in README about how to run tests, how to train new models, and the project architecture.
