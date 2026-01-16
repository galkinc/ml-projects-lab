# AWS Comprehend Medical Research

This directory contains research and a prototype for evaluating AWS Comprehend Medical for extracting medical entities from unstructured text.

## 1. Task Definition

**Objective**: To assess the capabilities of AWS Comprehend Medical for extracting medical entities (symptoms, diagnoses, medications, etc.) from unstructured texts (e.g., patient-doctor conversations) and determine the service's applicability within a potential LLM agent.

### Scope (MVP)
- **Language**: English only (as officially supported by Comprehend Medical).
- **Input**: Text messages (up to 10 KB per API call).
- **Output**: JSON with detected entities and their corresponding codes (SNOMED CT, ICD-10, etc.).
- **Out of Scope**: Audio/video processing, multilingual support, EHR integration, and HIPAA compliance setup at this stage.
- **Entity Detection**: `DetectEntitiesV2` -> returns entities like `MEDICAL_CONDITION`, `MEDICATION`, `TEST_TREATMENT_PROCEDURE`, `ANATOMY`, `PROTECTED_HEALTH_INFORMATION`.
- **Ontology Linking**:
  - `InferICD10CM` -> links conditions to ICD-10-CM codes.
  - `InferRxNorm` -> links medications to RxNorm.
  - `InferSNOMEDCT` -> links concepts to SNOMED CT.
- **Region**: Must use a supported region (e.g., `us-east-1`, `us-west-2`). Verify current list in AWS docs

### Success Criteria
- Successful API calls using `boto3`.
- Ability to receive and interpret medical entities from the response.
- Documentation in this README covering how to run the prototype, its limitations, cost estimates, and conclusions.

### Ethical & Regulatory Considerations Note
Per AWS documentation, Comprehend Medical outputs must not be used for direct clinical decision-making without human review. This prototype assumes downstream validation by qualified personnel.

## 2. Summary of Findings

The core outcome of this research is a detailed comparative analysis of the main Comprehend Medical APIs. The full analysis can be found in **[aws_comprehend_analysis.md](./aws_comprehend_analysis.md)**.

The key takeaways are:

*   **`DetectEntitiesV2`** is a general-purpose tool for identifying medical terms and PHI without linking them to a formal ontology. It is best for initial text processing and highlighting.
*   **`InferICD10CM`** is a specialized tool for mapping clinical conditions to the ICD-10-CM billing codes. It is essential for revenue cycle management and statistical reporting but ignores other entities.
*   **`InferRxNorm`** focuses exclusively on normalizing medications to RxNorm codes, which is critical for medication management and e-prescribing.
*   **`InferSNOMEDCT`** provides the most comprehensive semantic analysis by linking a wide range of medical concepts to the SNOMED-CT ontology. It is the most powerful tool for deep clinical data analysis but also the most complex.

The choice of API is not a matter of "which is best" but "which is right for the job." Our analysis provides a side-by-side comparison to help make that decision.

## 3. Research Steps

- [V] Review the [AWS Comprehend Medical Developer Guide](https://docs.aws.amazon.com/comprehend/latest/dg/comprehend-medical.html).
- [V] Identify supported entity types (e.g., `MEDICATION`, `MEDICAL_CONDITION`, `ANATOMY`), service limitations.
- [V] Develop a Python script (`main.py`) using `boto3` to call the `DetectEntitiesV2` or `InferICD10CM` API.
- [V] Test the script with a syntetic sample medical text.
- [V] Analyze the detected entities and their accuracy.
- [V] Evaluate the utility of normalization to SNOMED/ICD-10 codes.
- [V] Prepare The full analysis

## 4. Project Structure & Usage

This project is structured as a self-contained application managed by `uv`. The primary outcome of this research is the `aws_comprehend_analysis.md` file, which summarizes the findings.

### Project Structure

- `aws_comprehend_analysis.md`: **(Primary Artifact)** A detailed comparative analysis of the AWS Comprehend Medical APIs.
- `pyproject.toml`: Defines project metadata and Python dependencies.
- `config.py`: Loads settings from the `.env` file into a Pydantic `Settings` object.
- `main.py`: The main entry point to start an experiment via a command-line interface.
- `src/`: Contains the core application logic.
  - `main.py`: The main orchestrator that runs the experiment loop.
  - `aws.py`: Handles interaction with the Comprehend Medical API.
  - `io.py`: Handles file loading and saving of artifacts.
- `examples/`: Contains sample `.txt` files for analysis.
- `results/`: The output directory where all experiment artifacts are stored.

### How to Run

1.  **Prerequisites**: Ensure you have Python 3.13+ and `uv` installed.

2.  **Install Dependencies**: From the project root (`research/comprehend-medical-research`), create the virtual environment and install the required packages.
    ```sh
    uv venv
    uv sync
    ```

3.  **Configure Credentials**: Create a `.env` file in the project root (`research/comprehend-medical-research`) and add your AWS credentials:
    ```ini
    # .env
    AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_ACCESS_KEY"
    AWS_REGION="us-east-1"
    ```

4.  **Run the Experiment**: Execute the main script using `uv run`. You can specify which API to call using the `--api-method` (or `-a`) flag.

    *   **To detect general medical entities (default):**
        ```sh
        uv run python main.py --api-method entities
        ```

    *   **To infer ICD-10-CM codes for conditions:**
        ```sh
        uv run python main.py --api-method icd10
        ```

    *   **To infer RxNorm codes for medications:**
        ```sh
        uv run python main.py -a rxnorm
        ```
    
    *   **To infer SNOMED CT codes:**
        ```sh
        uv run python main.py -a snomedct
        ```

### Output Structure

The script saves detailed, versioned artifacts for each run to ensure reproducibility.

- `results/aws_comprehend/`: The root directory for all AWS Comprehend results.
  - `{dd_mm_yyyy}_{run_id}/`: A unique directory is created for each experiment run, named with the current date and a sequential run number for that day (e.g., `16_01_2026_1`).
    - `{index}_{example_name}/`: Inside the run directory, a sub-directory is created for each processed text file.
      - `input.json`: Contains the original text sent to the API, along with metadata like character count, timestamp, and the API method used.
      - `output.json`: Contains the full, raw JSON response received from the AWS Comprehend Medical API.


## Notes
- The service can detect Protected Health Information (PHI), but this prototype does not process real patient data and assumes synthetic or anonymized inputs 
- For texts longer than 10 KB, implement chunking logic with overlap to avoid splitting medical terms across segments
