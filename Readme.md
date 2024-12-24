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


# Setup Instructions:
There are some dependencies in requirements.txt that needs an older version of python: `3.12.7`
- Make a virtual environment using that version of python using:
```
python3.12 -m venv DiagnEnv
```
- Activate that virtual environment:
for macOS users:
```
source DiagnEnv/bin/activate
```
for Windows users:
```
source DiagnEnv/scripts/activate
```
- Install the dependencies in this virtual environment now:
```
pip install -r requirements.txt
```
- Create a file called `.env`, paste API keys for:
  - Anthropic : `CLAUDE_KEY = "sk-a...`
  - VoyageAI : `VOYAGE_API_KEY = "pa-a...` 
  - Path to the templates folder : `Template_path = "/Users/varun...` 
  - Path to the static folder : `Static_path = "/Users/varun`

<u>Note (For MacOS users)::</u><br>
If installing pyaudio gives an error then run `brew install portaudio`(make sure your DiagnAI virtual environment is active during this).
Then try `pip install pyaudio` again and it should work.

# Execution:
### Overall Pipeline:
[Click here to view the Pipeline Diagram](https://drive.google.com/file/d/1jK0IOxRMGhGNMcbyg_SrlvSrELqekcUQ/view?usp=share_link)

### Dataset:
Medically accurate corpus of data, focused on the real world medical practices. For example:
- Real past therapies are practiced by real therapists
- Patients' case studies
- Books and review papers

### Human Interaction:
- Real-time voice-to-voice interactions with RAG implemented with the new Claude Sonnet-3.5.
- The voice will mimic the real therapist(we will need to speak with doctors for it<personal_question>).

### Performance Evaluation:
- RAG evaluation libraries: giskard and ragas
- In our RAG evaluation we want to get a good analagous idea of false negatives and false positive cases.

### SPEECH TO SPEECH functionality using Google Cloud Text-to-speech API:
Estimation of inference time for audio generation are the following:
**__Short Sentences (a few words):__**
- Standard Voices: ~200-600 milliseconds
- Neural Voices: ~500-1000 milliseconds
**__Medium Sentences (a few sentences):__**
- Standard Voices: ~500 milliseconds - 2 seconds
- Neural Voices: ~1-3 seconds
__**Long Sentences (a paragraph or more):**__
- Standard Voices: ~1-5 seconds
- Neural Voices: ~2-10+ seconds

### Front End:
- Default Streamlit template.

### Backend & User Database:
- A common table for User's information
- Individual tables for each user.

### Model Deployment:
- Containerize the project environment using Docker.
- Deploying it using free googleGCP(Google Cloud Platform) credits.

<hr>

## Scope of DiagnAI:
- Real-time photorealistic face generation with facial expressions.
- Multimodal Diagnosis with all sorts of clinical medical reports:
  - Vital Signs
  - EEG
  - Blood Test Reports
  - X-Rays
  - MRIs
  - Ultrasounds
  - etc.
