This is our AI ATL 2024 Project. It's called `DiagnAI` representing `Diagnosis + AI`.

<img src="https://github.com/user-attachments/assets/04ee3227-27df-458e-8aec-6dca25b12330" alt="Logo" width="30%">

# DiagnAI's Capabilities:
### Initial Screening:
- We can help doctors in making their professional workflow more efficient.
- We can have patients get a better idea of their potential condition to narrow down onto one particular medical specialist like a psychaitrist or orthopedic.
### Early Disease Detection:
- We will reduce the cases when the user don't know about their developing medical condition, but it needs medical attention.
- Philosophy: Easier to cure the earlier it's detected.
### Mental Health Companion:
- Can conversationally understand the user's current situation and send timely summary reports to the doctor.
- Can execute complementary follow up therapies.
### 24*7 Available Health Guide:
- 24*7 availability to context aware, accurate daily life health tips.

The model can be a regular companion of the user and can detect if something is wrong with the user.
We can take away the initial screening pressure from the medical industry so that they can just focus on saving lives. And we can let highly specialized LLM agents do the initial medical screening.
Regular therapies have a higher frequency than a therapist can provide.



## Execution:
### Dataset:
Medically accurate corpus of data, focused on the real world medical practices. For example:
- Real past therapies are practiced by real therapists
- Patients' case studies
- Books and review papers

### Human Interaction:
Real-time voice-to-voice interactions with RAG implemented with the new Claude Sonnet-3.5.

The voice will mimic the real therapist(we will need to speak with doctors for it).

### Overall Pipeline:
[https://drive.google.com/file/d/1jK0IOxRMGhGNMcbyg_SrlvSrELqekcUQ/view?usp=share_link](pipeline diagram)

### Performance Evaluation:
- RAG evaluation library: giskard
- In our RAG evaluation we want to get a good analagous idea of false negatives and false positive cases.

### Front End:
- Default Streamlit template.
### Backend & User Database:
- A common table for User's information
- Individual tables for each user.

### Model Deployment:
- Containerize the project environment using Docker.
- Deploying it using free googleGCP(Google Cloud Platform) credits.

<hr>

### Scope:
- Real-time photorealistic face generation with facial expressions.
- Multimodal Diagnosis with all sorts of clinical medical reports:
  - Vital Signs
  - EEG
  - Blood Test Reports
  - X-Rays
  - MRIs
  - Ultrasounds
  - etc.
