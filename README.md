# Extract API Setup Guide

This project requires a Python virtual environment and several dependencies. Please follow the steps below to set up your development environment:

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:

   - On Windows (may require administrator privileges):
     ```bash
     .venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

3. Install the required version of pip:

   ```bash
   pip install "pip<24.1"
   ```

4. Install project dependencies:
   ```bash
   pip install textract
   ```
