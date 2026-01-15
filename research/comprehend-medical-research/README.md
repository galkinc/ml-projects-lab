# AWS Comprehend Medical Research

This directory contains research and a prototype for evaluating AWS Comprehend Medical for extracting medical entities from unstructured text.

## 1. Task Definition

**Objective**: To assess the capabilities of AWS Comprehend Medical for extracting medical entities (symptoms, diagnoses, medications, etc.) from unstructured texts (e.g., patient-doctor conversations) and determine the service's applicability within a potential LLM agent.

### Scope (MVP)
- **Language**: English only (as officially supported by Comprehend Medical).
- **Input**: Text messages (up to 10 KB per API call).
- **Output**: JSON with detected entities and their corresponding codes (SNOMED CT, ICD-10, etc.).
- **Out of Scope**: Audio/video processing, multilingual support, EHR integration, and HIPAA compliance setup at this stage.
- **Entity Detection**: `DetectEntitiesV2` → returns entities like `MEDICAL_CONDITION`, `MEDICATION`, `TEST_TREATMENT_PROCEDURE`, `ANATOMY`, `PROTECTED_HEALTH_INFORMATION`.
- **Ontology Linking**:
  - `InferICD10CM` → links conditions to ICD-10-CM codes.
  - `InferRxNorm` → links medications to RxNorm.
  - `InferSNOMEDCT` → links concepts to SNOMED CT.
- **Region**: Must use a supported region (e.g., `us-east-1`, `us-west-2`). Verify current list in AWS docs

### Success Criteria
- Successful API calls using `boto3`.
- Ability to receive and interpret medical entities from the response.
- A high-level comparison of accuracy/completeness with an open-source alternative (e.g., scispaCy, BioBERT) on at least one sample text
  - Qualitative assessment: Does Comprehend Medical capture clinically relevant symptoms that open-source models miss (or vice versa)
  - False positive/negative examples documented in `results/`.
- Documentation in this README covering how to run the prototype, its limitations, cost estimates, and conclusions.

### Ethical & Regulatory Considerations Note
Per AWS documentation, Comprehend Medical outputs must not be used for direct clinical decision-making without human review. This prototype assumes downstream validation by qualified personnel.

## 2. Research Steps

### A. Documentation Review
- [ ] Review the [AWS Comprehend Medical Developer Guide](https://docs.aws.amazon.com/comprehend/latest/dg/comprehend-medical.html).
- [ ] Identify supported entity types (e.g., `MEDICATION`, `MEDICAL_CONDITION`, `ANATOMY`).
- [ ] Note service limitations (text length, language, regions).
- [ ] Check the latest pricing details.

### B. Access Configuration
- [ ] Create an IAM user or role with the `ComprehendMedicalFullAccess` policy.
- [ ] Configure AWS credentials locally (e.g., in `~/.aws/credentials`).

### C. Python Prototype
- [ ] Develop a Python script (`main.py`) using `boto3` to call the `DetectEntitiesV2` or `InferICD10CM` API.
- [ ] Test the script with a sample medical text.

### D. Results Analysis
- [ ] Analyze the detected entities and their accuracy.
- [ ] Evaluate the utility of normalization to SNOMED/ICD-10 codes.
- [ ] Assess the usefulness of the confidence scores for filtering results.

### E. Comparative Analysis (Optional)
- [ ] Process the same sample text using an open-source library like `scispaCy`.
- [ ] Compare the recall/precision of the outputs.

## 3. Artifacts

- **`main.py`**: The Python script for the prototype.
- **`README.md`**: This documentation file.
- **`examples/`**: (To be created) A directory for sample input texts.
- **`results/`**: (To be created) A directory for storing JSON outputs from the API.

  results/
    ├── aws_comprehend/
    │   └── sample1.json
    └── scispacy/
        └── sample1.json

## 4. Next Steps (Roadmap)

- **LLM Agent Integration**: Use Comprehend Medical as a "ground truth extractor" for RAG or evaluation.
- **Video-to-Text Pipeline**: Explore a pipeline: Video -> Whisper for transcription -> Comprehend Medical for entity extraction.
- **Alternative Services**: Investigate alternatives like Google Cloud Healthcare API or Azure Text Analytics for Health.

## Notes
- The service can detect Protected Health Information (PHI), but this prototype does not process real patient data and assumes synthetic or anonymized inputs 
- For texts longer than 10 KB, implement chunking logic with overlap to avoid splitting medical terms across segments
