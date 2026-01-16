# Analysis of AWS Comprehend Medical APIs

This document provides a comparative analysis of the different APIs available in AWS Comprehend Medical, based on experiments conducted on synthetic clinical notes.

## 1. Executive Summary

DetectEntitiesV2 provides broad entity extraction without ontologies. Ontology-linked APIs (InferICD10CM, InferRxNorm, InferSNOMEDCT) add semantic normalization but are category-specific.

---

## 2. Comparison by API Method

This section details the specific strengths, weaknesses, and ideal use cases for each API endpoint.

### a. DetectEntitiesV2 (`entities`)

-   **Use Case**: Synchronous analysis of clinical text to detect medical entities across 7 entity categories. Commonly used when applications need to know that a medical concept is present in free text without mapping it to standardized codes.
-   **Links for details**: 
    - [https://docs.aws.amazon.com/comprehend-medical/latest/api/API_DetectEntitiesV2.html](https://docs.aws.amazon.com/comprehend-medical/latest/api/API_DetectEntitiesV2.html)
    - [Entities Categories](https://docs.aws.amazon.com/comprehend-medical/latest/dev/textanalysis-entitiesv2.html)
-   **Strengths**:
    - Detects a broad range of clinical entities, including PHI and behavioral/environmental/social factors.
    - Returns structured output with entity text, category, type, character offsets, confidence scores, attributes (for example DOSAGE, ACUITY, DIRECTION), traits (for example NEGATION), and relationship types between entities and attributes, each with its own confidence score.
-   **Constraints**:
    - Does not return standardized medical codes such as ICD-10 or SNOMED; output is text-based (for example, "headache" and synonyms are separate strings).
    - Supports English-language clinical text only and synchronous requests up to 20,000 bytes per call.
    - For batch processing, a separate asynchronous operation `StartEntitiesDetectionV2Job` must be used instead of `DetectEntitiesV2`.
    - Entity categories are fixed to the service-defined set: [ANATOMY, BEHAVIORAL_ENVIRONMENTAL_SOCIAL, MEDICAL_CONDITION, MEDICATION, PROTECTED_HEALTH_INFORMATION, TEST_TREATMENT_PROCEDURE, TIME_EXPRESSION](https://docs.aws.amazon.com/comprehend-medical/latest/dev/textanalysis-entitiesv2.html)

### b. InferICD10CM (`icd10`)

-   **Use Case**: Synchronous analysis of clinical text to detect MEDICAL_CONDITION entities of type `DX_NAME` and link them to ICD-10-CM codes, including code descriptions ranked by confidence. Commonly used for medical coding assistance, clinical studies/trials, population health management, early detection, and integration with healthcare systems.
-   **Links for details**: [https://docs.aws.amazon.com/comprehend-medical/latest/api/API_InferICD10CM.html](https://docs.aws.amazon.com/comprehend-medical/latest/api/API_InferICD10CM.html)
-   **Strengths**:
    - Returns normalized ICD-10-CM concepts (Code, Description, Score) for each detected condition.
    - Captures contextual traits (DIAGNOSIS, SIGN, SYMPTOM, NEGATION (LOW_CONFIDENCE, PERTAINS_TO_FAMILY, HYPOTHETICAL)) and attributes (ACUITY, DIRECTION, SYSTEM_ORGAN_SITE (QUALITY, QUANTITY, TIME_TO_DX_NAME, TIME_EXPRESSION, RELATIONSHIP_TYPE)), each with dedicated confidence and relationship scores.
-   **Constraints**:
    - Focuses exclusively on `MEDICAL_CONDITION` category; does not detect medications, procedures, anatomy, or PHI.
    - Outputs ICD-10-CM codes only; no support for other systems (e.g., SNOMED, RxNorm).
    - English-language clinical text only; input length 1–10,000 characters per synchronous call (use `StartICD10CMInferenceJob` for batch).
    - Entity categories limited to `MEDICAL_CONDITION`.

### c. InferRxNorm (`rxnorm`)

-   **Use Case**: Detects medications. Synchronous analysis of clinical text to detect medication entities and link them to normalized RxNorm concept identifiers (`RxCUI` codes) from the National Library of Medicine.
-   **Links for details**: [https://docs.aws.amazon.com/comprehend-medical/latest/api/API_InferRxNorm.html](https://docs.aws.amazon.com/comprehend-medical/latest/api/API_InferRxNorm.html)
-   **Strengths**:
    - Returns medication entities with RxNormConcepts (code, description, score), attributes (e.g., DOSAGE, FORM, STRENGTH), traits (e.g., NEGATION), and relationship scores.
    - Supports pagination for large results.
-   **Constraints**:
    -   Only focuses on medications. All other medical information in the text is ignored.
    - English-only clinical text, 1–10,000 characters per request.
    - For batch processing, use `StartRxNormInferenceJob`.

### d. InferSNOMEDCT (`snomedct`)

-   **Use Case**: Synchronous analysis to detect medical concepts and link them to SNOMED-CT codes (top matches with scores), covering categories like MEDICAL_CONDITION, ANATOMY, TEST_TREATMENT_PROCEDURE.
- **Links for details**: 
    - [https://docs.aws.amazon.com/comprehend-medical/latest/api/API_InferSNOMEDCT.html](https://docs.aws.amazon.com/comprehend-medical/latest/api/API_InferSNOMEDCT.html)
    - [https://docs.aws.amazon.com/cli/latest/reference/comprehendmedical/infer-snomedct.html](https://docs.aws.amazon.com/cli/latest/reference/comprehendmedical/infer-snomedct.html)
-   **Strengths**:
    - Returns entities with SNOMEDCTConcepts (code, description, score), attributes, traits, relationship types/scores, and SNOMEDCTDetails (edition, language, version).
    - Supports pagination; available in US regions
-   **Constraints**:
    - Limited to specific categories (MEDICAL_CONDITION, ANATOMY, TEST_TREATMENT_PROCEDURE).
    - English-only clinical text, **1–5,000 characters**; US-only availability
    - For batch processing, use `StartSNOMEDCTInferenceJob`.

---

## 3. API Comparison Table


| API                | Primary Focus                          | Ontology       | Max Sync Length | Batch Job API                     | Regional Availability |
|--------------------|----------------------------------------|----------------|-----------------|-----------------------------------|----------------------|
| DetectEntitiesV2  | All 7 categories + PHI                | None           | 20 KB   | StartEntitiesDetectionV2Job      | Global              |
| InferICD10CM      | MEDICAL_CONDITION (DX_NAME)           | ICD-10-CM      | 10 KB   | StartICD10CMInferenceJob         | Global              |
| InferRxNorm       | MEDICATION                            | RxNorm (RxCUI) | 10 KB   | StartRxNormInferenceJob          | Global              |
| InferSNOMEDCT     | MEDICAL_CONDITION, ANATOMY, TEST_TREATMENT_PROCEDURE | SNOMED-CT | 5 KB    | StartSNOMEDCTInferenceJob        | US Regions    |

---

## 4. Side-by-Side Example Analysis

This section provides a direct comparison of the outputs from each API for a single text sample to illustrate the differences in a practical way.

### `1_synthetic_patient_gastritis.txt`
> For the past three days, I have had a burning pain in the upper part of my stomach. The pain gets worse after eating and is sometimes accompanied by nausea. I feel bloated and uncomfortable, especially in the epigastric area. There is no vomiting or fever.

| Text Snippet                 | `DetectEntitiesV2`<br>*(What?)*                     | `InferICD10CM`<br>*(Billing/Stats)*               | `InferRxNorm`<br>*(Medications)* | `InferSNOMEDCT`<br>*(Clinical Detail)*          |
|------------------------------|---------------------------------------------------|--------------------------------------------------|----------------------------------|------------------------------------------------|
| **burning pain**             | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`           | `R10.10`<br>*Upper abdominal pain, unspecified*  | —                                | `36349006`<br>*Burning pain (finding)*         |
| **upper part of my stomach** | `ANATOMY`<br>`Type: SYSTEM_ORGAN_SITE`            | —                                                | —                                | `361534007`<br>*Structure of upper body of stomach* |
| **nausea**                   | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`           | `R11.0`<br>*Nausea*                              | —                                | `422587007`<br>*Nausea (finding)*              |
| **bloated**                  | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`           | `R14.0`<br>*Abdominal distension (gaseous)*      | —                                | `248490000`<br>*Bloating symptom (finding)*    |
| **vomiting**                 | `MEDICAL_CONDITION`<br>`Traits: SYMPTOM, NEGATION`| `R11.10`<br>*Vomiting, unspecified*              | —                                | `249497008`<br>*Vomiting symptom (finding)*    |
| **fever**                    | `MEDICAL_CONDITION`<br>`Traits: SYMPTOM, NEGATION`| `R50.9`<br>*Fever, unspecified*                  | —                                | `386661006`<br>*Fever (finding)*               |

### `2_synthetic_patient_rib_fracture.txt`
> I fell off my bike yesterday and landed on my right side. Now I have sharp, stabbing pain in my right chest that gets worse when I take a deep breath or cough. There is no shortness of breath, but I feel tender to touch over the 5th rib. No history of osteoporosis.

| Text Snippet                     | `DetectEntitiesV2`<br>*(What?)*                                  | `InferICD10CM`<br>*(Billing/Stats)*                              | `InferRxNorm`<br>*(Medications)* | `InferSNOMEDCT`<br>*(Clinical Detail)*                     |
|----------------------------------|------------------------------------------------------------------|------------------------------------------------------------------|----------------------------------|-----------------------------------------------------------|
| **sharp, stabbing pain**         | `MEDICAL_CONDITION`<br>`Traits: SYMPTOM`                         | `R07.9`<br>*Chest pain, unspecified*                             | —                                | `285386001`<br>*Right sided chest pain (finding)*         |
| **right chest**                  | `ANATOMY`<br>`Type: SYSTEM_ORGAN_SITE`                           | —                                                                | —                                | `771319006`<br>*Structure of right half of chest wall*    |
| **5th rib**                      | `ANATOMY`<br>`Type: SYSTEM_ORGAN_SITE`                           | —                                                                | —                                | `15339008`<br>*Bone structure of fifth rib (body structure)* |
| **tender to touch**              | `MEDICAL_CONDITION`<br>`Traits: SYMPTOM`                         | `R07.81`<br>*Pleurodynia*                                        | —                                | `298740004`<br>*Rib tender (finding)*                     |
| **shortness of breath**          | `MEDICAL_CONDITION`<br>`Traits: SYMPTOM, NEGATION`               | `R06.02`<br>*Shortness of breath*                                | —                                | `267036007`<br>*Dyspnea (finding)*                        |
| **osteoporosis**                 | `MEDICAL_CONDITION`<br>`Traits: DIAGNOSIS, NEGATION`             | `M81.0`<br>*Age-related osteoporosis without current pathological fracture* | —                                | `64859006`<br>*Osteoporosis (disorder)*                   |

### `3_synthetic_patient_anxiety_disorder.txt`
> For the last two weeks, I've been feeling constantly worried and on edge. I have trouble sleeping, often wake up with racing thoughts, and sometimes experience heart palpitations. I don't feel sad, but I'm easily irritable and avoid social gatherings. No panic attacks reported.

| Text Snippet             | `DetectEntitiesV2`<br>*(What?)*                     | `InferICD10CM`<br>*(Billing/Stats)*               | `InferRxNorm`<br>*(Medications)* | `InferSNOMEDCT`<br>*(Clinical Detail)*          |
|--------------------------|---------------------------------------------------|--------------------------------------------------|----------------------------------|------------------------------------------------|
| **worried**              | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`           | `R45.82`<br>*Worries*                            | —                                | `79015004`<br>*Worried (finding)*              |
| **on edge**              | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`           | `R46.6`<br>*Undue concern with stressful events*  | —                                | `40917007`<br>*Clouded consciousness*         |
| **trouble sleeping**     | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`           | `G47.00`<br>*Insomnia, unspecified*              | —                                | `301345002`<br>*Difficulty sleeping*          |
| **racing thoughts**      | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`           | `R41.89`<br>*Other symptoms involving cognition*  | —                                | `285303006`<br>*Racing thoughts*              |
| **heart palpitations**   | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`<br>+ `ANATOMY: heart` | `R00.2`<br>*Palpitations*                        | —                                | `80313002`<br>*Palpitations (finding)*        |
| **feel sad**             | `MEDICAL_CONDITION`<br>`Traits: SYMPTOM, NEGATION`| `R45.2`<br>*Unhappiness*                         | —                                | `420038007`<br>*Feeling unhappy*              |
| **easily irritable**     | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`           | `R45.4`<br>*Irritability and anger*              | —                                | `55929007`<br>*Feeling irritable*             |
| **panic attacks**        | `MEDICAL_CONDITION`<br>`Traits: SYMPTOM, NEGATION`| `F41.0`<br>*Panic disorder [episodic anxiety]*    | —                                | `225624000`<br>*Panic attack (finding)*       |

### `4_synthetic_patient_wellness_check.txt`
> I am here for my annual physical exam. I feel generally healthy, exercise 3 times a week, and eat a balanced diet. No chest pain, no headaches, no fatigue. I take a daily multivitamin and occasional ibuprofen for muscle soreness after workouts. Family history: mother has hypertension.

| Text Snippet                 | `DetectEntitiesV2`<br>*(What?)*                     | `InferICD10CM`<br>*(Billing/Stats)*               | `InferRxNorm`<br>*(Medications)* | `InferSNOMEDCT`<br>*(Clinical Detail)*          |
|------------------------------|---------------------------------------------------|--------------------------------------------------|----------------------------------|------------------------------------------------|
| **physical exam**            | `TEST_TREATMENT_PROCEDURE`<br>`Type: TEST_NAME`   | —                                                | —                                | `5880005`<br>*Physical examination procedure* |
| **feel generally healthy**   | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`           | `R69`<br>*Illness, unspecified*                  | —                                | `135815002`<br>*General health good (finding)* |
| **exercise**                 | `TEST_TREATMENT_PROCEDURE`<br>`Type: TREATMENT_NAME` | —                                             | —                                | `61686008`<br>*Physical exercise (observable entity)* |
| **eat a balanced diet**      | `TEST_TREATMENT_PROCEDURE`<br>`Type: TREATMENT_NAME` | —                                             | —                                | `226229006`<br>*Balanced diet (finding)*      |
| **chest pain**               | `MEDICAL_CONDITION`<br>`Traits: SYMPTOM, NEGATION`| `R07.9`<br>*Chest pain, unspecified*             | —                                | `29857009`<br>*Chest pain (finding)*          |
| **headaches**                | `MEDICAL_CONDITION`<br>`Traits: SYMPTOM, NEGATION`| `R51.9`<br>*Headache, unspecified*               | —                                | `25064002`<br>*Headache (finding)*            |
| **fatigue**                  | `MEDICAL_CONDITION`<br>`Traits: SYMPTOM, NEGATION`| `R53.83`<br>*Other fatigue*                      | —                                | `84229001`<br>*Fatigue (finding)*             |
| **multivitamin**             | `MEDICATION`<br>`Type: GENERIC_NAME`              | —                                                | `11251`<br>*vitamin b complex*   | —                                              |
| **ibuprofen**                | `MEDICATION`<br>`Type: GENERIC_NAME`              | —                                                | `5640`<br>**ibuprofen**          | —                                              |
| **muscle soreness**          | `MEDICAL_CONDITION`<br>`Trait: SYMPTOM`           | `M79.10`<br>*Myalgia, unspecified site*          | —                                | `68962001`<br>*Muscle pain (finding)*         |
| **hypertension**<br>(family) | `MEDICAL_CONDITION`<br>`Traits: DIAGNOSIS, PERTAINS_TO_FAMILY` | `Z82.49`<br>*Family history of circulatory disease* | —                          | `160357008`<br>**Family history: Hypertension** |