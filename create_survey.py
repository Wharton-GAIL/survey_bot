import os
import sys
import requests
import json
from google import genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ───────── SET UP QUALTRICS & GEMINI ───────────────

# Gemini client
CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# If you store your token in an environment variable, you can read it here:
QUALTRICS_TOKEN = os.getenv("QUALTRICS_TOKEN")

DATA_CENTER = 'co1'  # e.g., "iad1", "ca1", "eu1", etc.
BASE_URL = f'https://{DATA_CENTER}.qualtrics.com/API/v3'
HEADERS = {
    "x-api-token": QUALTRICS_TOKEN,
}

# ───────── SURVEY CONSTRUCTION FUNCTIONS ───────────────


def create_mc_question_block(question_id, label, question_text, response_options, survey_id="SV_6XMOJPHrKo918fI"):
    '''
    Function to create a multiple choice question block in QSF format
    Returns question blocks
    '''

    # Create the response options in the QSF format
    choices = {str(i+1): {"Display": option} for i, option in enumerate(response_options.split(", "))}
    
    question_block = {
        "SurveyID": survey_id,
        "Element": "SQ",  # Survey Question element
        "PrimaryAttribute": f"QID{question_id}",
        "Payload": {
            "QuestionText": question_text,
            "DefaultChoices": False,
            "DataExportTag": label,
            "QuestionType": "MC",  # Multiple Choice
            "Selector": "SAVR",  # Single Answer Vertical
            "SubSelector": "TX",  # Text-based
            "Configuration": {
                "QuestionDescriptionOption": "UseText"
            },
            "QuestionDescription": label,
            "Choices": choices,  # Response options
            "ChoiceOrder": [str(i+1) for i in range(len(choices))],
            "Validation": {
                "Settings": {
                    "ForceResponse": "OFF",
                    "Type": "None"
                }
            },
            "Language": [],
            "NextChoiceId": len(choices) + 1,
            "NextAnswerId": 1,
            "QuestionID": f"QID{question_id}",
        }
    }
    return question_block

def create_short_survey_from_string(survey_data_string):
    '''
    Creates in AI response to generate short multiple-choice survey
    '''

    # Split the input string by the pipe ("|") character.

    # Remove trailing pipe if it exists
    if survey_data_string.endswith("|"):
        survey_data_string = survey_data_string[:-1]

    # We expect exactly 12 parts (4 per question x 3 questions).
    parts = survey_data_string.split("|")
    survey_blocks = []

    if parts and parts[-1].strip() == "":
        parts.pop()

    if len(parts) % 4 != 0:
        raise ValueError(
            "Gemini formatted the survey incorrectly, please try again. :("
        )
        
    # Process every group of 4
    for i in range(0, len(parts), 4):
        q_id = parts[i]
        q_label = parts[i + 1]
        q_text = parts[i + 2]
        q_options = parts[i + 3]

        # Create a MC question block using your helper function
        survey_blocks.append(
            create_mc_question_block(
                question_id=int(q_id),
                label=q_label,
                question_text=q_text,
                response_options=q_options
            )
        )

    num_questions = len(survey_blocks)
    return num_questions, survey_blocks

def create_qsf_file(
    questions,
    output_filename='qsf_files/generated_survey.qsf',
    survey_id="SV_6XMOJPHrKo918fI",
    survey_name="Auto-Generated Survey",
    survey_owner="UR_5nGkW5NZ9iaHrtc",
    survey_brand="wharton",
    survey_status="Inactive",
    survey_start_date="0000-00-00 00:00:00",
    survey_expiration_date="0000-00-00 00:00:00",
    survey_creation_date="2025-02-16 16:51:58",
    survey_language="EN"
):
    """
    Creates a QSF file that matches the structure of your 'working QSF':
      1) A Survey Blocks (BL) element with a Default block referencing question IDs.
      2) A Survey Flow (FL) referencing that default block ID.
      3) Standard elements (SO, STAT, QC, RS, SCO, etc.).
      4) Appended question elements (SQ).
    """

    # --- Prepare a block ID (match your reference's ID if desired) ---
    default_block_id = "BL_1YecbDaQMp1nXX8"

    # Build the "Survey Blocks" element. Notice the array for "Payload" and two blocks: Default & Trash
    survey_blocks_element = {
        "SurveyID": survey_id,
        "Element": "BL",
        "PrimaryAttribute": "Survey Blocks",
        "SecondaryAttribute": None,
        "TertiaryAttribute": None,
        "Payload": [
            {
                "Type": "Default",
                "Description": "Default Question Block",
                "ID": default_block_id,
                "BlockElements": [
                    # We create a "Type":"Question" entry for each QID in the questions list
                    {"Type": "Question", "QuestionID": q["Payload"]["QuestionID"]}
                    for q in questions
                ]
            },
            {
                "Type": "Trash",
                "Description": "Trash / Unused Questions",
                "ID": "BL_bxQacfQHYYQQwm2"
            }
        ]
    }

    # Build the Survey Flow (FL) element that references the default block
    survey_flow_element = {
        "SurveyID": survey_id,
        "Element": "FL",
        "PrimaryAttribute": "Survey Flow",
        "SecondaryAttribute": None,
        "TertiaryAttribute": None,
        "Payload": {
            "Flow": [
                {
                    "ID": default_block_id,  # reference the Default block
                    "Type": "Block",
                    "FlowID": "FL_2"
                }
            ],
            "Properties": {
                "Count": 3
            },
            "FlowID": "FL_1",
            "Type": "Root"
        }
    }

    # Example QC element (Survey Question Count) – set to length of `questions`
    question_count_element = {
        "SurveyID": survey_id,
        "Element": "QC",
        "PrimaryAttribute": "Survey Question Count",
        "SecondaryAttribute": str(len(questions)),
        "TertiaryAttribute": None,
        "Payload": None
    }

    # Example RS element
    rs_element = {
        "SurveyID": survey_id,
        "Element": "RS",
        "PrimaryAttribute": "RS_bknoxgAY3lNkLtA",
        "SecondaryAttribute": "Default Response Set",
        "TertiaryAttribute": None,
        "Payload": None
    }

    # Example SCO (scoring) element
    sco_element = {
        "SurveyID": survey_id,
        "Element": "SCO",
        "PrimaryAttribute": "Scoring",
        "SecondaryAttribute": None,
        "TertiaryAttribute": None,
        "Payload": {
            "ScoringCategories": [],
            "ScoringCategoryGroups": [],
            "ScoringSummaryCategory": None,
            "ScoringSummaryAfterQuestions": 0,
            "ScoringSummaryAfterSurvey": 0,
            "DefaultScoringCategory": None,
            "AutoScoringCategory": None
        }
    }

    # Example SO (Survey Options) element
    so_element = {
        "SurveyID": survey_id,
        "Element": "SO",
        "PrimaryAttribute": "Survey Options",
        "SecondaryAttribute": None,
        "TertiaryAttribute": None,
        "Payload": {
            "BackButton": "false",
            "SaveAndContinue": "true",
            "SurveyProtection": "PublicSurvey",
            "BallotBoxStuffingPrevention": "false",
            "NoIndex": "Yes",
            "SecureResponseFiles": "true",
            "SurveyExpiration": "None",
            "SurveyTermination": "DefaultMessage",
            "Header": "",
            "Footer": "",
            "ProgressBarDisplay": "None",
            "PartialData": "+1 week",
            "ValidationMessage": "",
            "PreviousButton": "",
            "NextButton": "",
            "SurveyTitle": "Qualtrics Survey | Qualtrics Experience Management",
            "SkinLibrary": survey_brand,
            "SkinType": "templated",
            "Skin": {
                "brandingId": "6138034454",
                "templateId": "*base",
                "overrides": None
            },
            "NewScoring": 1,
            "SurveyMetaDescription": "The most powerful, simple and trusted way to gather experience data."
        }
    }

    # Example STAT element (Survey Statistics)
    stat_element = {
        "SurveyID": survey_id,
        "Element": "STAT",
        "PrimaryAttribute": "Survey Statistics",
        "SecondaryAttribute": None,
        "TertiaryAttribute": None,
        "Payload": {
            "MobileCompatible": True,
            "ID": "Survey Statistics"
        }
    }

    # Optionally add a "PROJ" or "PL" or "NT" element to replicate your reference QSF exactly:
    proj_element = {
        "SurveyID": survey_id,
        "Element": "PROJ",
        "PrimaryAttribute": "CORE",
        "SecondaryAttribute": None,
        "TertiaryAttribute": "1.1.0",
        "Payload": {
            "ProjectCategory": "CORE",
            "SchemaVersion": "1.1.0"
        }
    }
    # (Add more optional items like "PL" or "NT" if you need them.)

    # -----------------------------------------------------------------------------------------
    # Now assemble the final QSF structure in the same order as your reference:
    #   1) Survey Blocks (BL)
    #   2) Survey Flow (FL)
    #   3) PROJ (or others like NT, PL) if desired
    #   4) QC, RS, SCO, SO
    #   5) The actual question elements (SQ) come last or anywhere in SurveyElements
    #   6) STAT
    # -----------------------------------------------------------------------------------------
    qsf_structure = {
        "SurveyEntry": {
            "SurveyID": survey_id,
            "SurveyName": survey_name,
            "SurveyDescription": None,
            "SurveyOwnerID": survey_owner,
            "SurveyBrandID": survey_brand,
            "DivisionID": None,
            "SurveyLanguage": survey_language,
            "SurveyActiveResponseSet": "RS_bknoxgAY3lNkLtA",
            "SurveyStatus": survey_status,
            "SurveyStartDate": survey_start_date,
            "SurveyExpirationDate": survey_expiration_date,
            "SurveyCreationDate": survey_creation_date,
            "CreatorID": survey_owner,
            "LastModified": "2025-02-16 17:28:17",
            "LastAccessed": "0000-00-00 00:00:00",
            "LastActivated": "0000-00-00 00:00:00",
            "Deleted": None
        },
        "SurveyElements": [
            survey_blocks_element,      # "BL"
            survey_flow_element,       # "FL"
            proj_element,              # "PROJ" (optional, but included for matching your reference)
            question_count_element,    # "QC"
            rs_element,                # "RS"
            sco_element,               # "SCO"
            so_element,                # "SO"

            # Add the question elements (SQ) themselves
            # Make sure each item in `questions` is an "SQ" element with matching QID in the Payload
            *questions,

            # Finally the STAT element:
            stat_element
        ]
    }
    
    # Write to disk
    import os, json
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, 'w') as outfile:
        json.dump(qsf_structure, outfile, indent=2)

    print(f"[INFO] QSF file created at: {output_filename}")
    return output_filename

def ideate_survey_mc(topic, info): 
    '''
    Generate **multiple-choice** survey and present to user for feedback 
    Returns the survey as a string
    '''

    user_message = "Create a 5-question survey about " + topic + " using the following clarifying information: " + info
    bot_message = user_message + " Return only the survey questions in your response, all of which should be multiple choice with letter options (do not use the all-of-the-above answer choice). Your response will be fed directly into a program."

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    return str(response.text)

def ideate_survey_likert(topic, info):
    '''
    Generate **likert-scale** survey and present to user for feedback 
    Returns the survey as a string
    '''

    user_message = "Come up with 5 statements about " + topic + " for a Likert-scale grid survey using the following clarifying information: " + info
    bot_message = user_message + " Return only the statements in your response. Your response will be fed directly into a program."

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    out_text = "The possible responses for each statement are: Strongly Disagree, Disagree, Neutral, Agree, Strongly Agree.\n" + str(response.text)
    return out_text

def clarify_survey(topic): 
    '''
    Propose clarifying questions to ask the user in response to survey request
    Returns questions as a string
    '''

    message = "I was asked to create a survey about" + topic + ". Give me 2-4 clarifying questions about the survey content (e.g. Things to ask, clarify subject, etc) that I can ask the requestor."

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=message
    )

    return str(response.text)

def revise_survey(survey, revision):
    '''
    Edit existing survey draft
    Returns survey as a string
    '''

    # here's the survey, here's the revision, please fix and return the survey 
    bot_message = "Here's a survey: " + survey + "\n Make the following revisions (but keep the survey multiple-choice with letter options). Return only the survey questions in your response as it will be fed directly into a program: " + revision

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    return str(response.text)

def create_likert_matrix_question_block(
        question_id: int,
        label: str,
        question_text: str,
        statements: list[str],             # rows
        scale_options: list[str],          # columns (e.g., ["Strongly Disagree", ...]
        single_answer: bool = True,
        survey_id: str = "SV_6XMOJPHrKo918fI"
):
    """
    Build a Qualtrics matrix (grid) question formatted as a Likert scale.

    Parameters
    ----------
    question_id     Numeric ID (int) – becomes QID{question_id}
    label           Data-export tag (string) – no spaces
    question_text   Prompt shown above the grid
    statements      List of row labels / sub-questions (one per row)
    scale_options   List of Likert choices shown as columns (left→right)
    single_answer   True  = one choice per row (Likert SA)
                    False = multi-select per row (Likert MA)
    survey_id       Qualtrics survey ID (default kept from your script)

    Returns
    -------
    dict – JSON fragment ready to append to `SurveyElements`
    """

    # Columns (Choices) – keys must be strings starting at "1"
    choices = {str(i + 1): {"Display": col}            for i, col in enumerate(statements)}
    # Rows (Answers / “Statements”)
    answers = {str(i + 1): {"Display": row}            for i, row in enumerate(scale_options)}

    matrix_block = {
        "SurveyID": survey_id,
        "Element": "SQ",
        "PrimaryAttribute": f"QID{question_id}",
        "Payload": {
            "QuestionText": question_text,
            "DataExportTag": label,
            "QuestionType": "Matrix",
            "Selector": "Likert",
            "SubSelector": "SingleAnswer" if single_answer else "MultipleAnswer",
            "Configuration": {
                "QuestionDescriptionOption": "UseText"
            },
            "QuestionDescription": label,
            "Choices": choices,                # columns
            "ChoiceOrder": list(choices.keys()),
            "Answers": answers,                # rows
            "AnswerOrder": list(answers.keys()),
            "Validation": {
                "Settings": {
                    "ForceResponse": "OFF",
                    "Type": "None"
                }
            },
            "Language": [],
            "NextChoiceId": len(choices) + 1,
            "NextAnswerId": len(answers) + 1,
            "QuestionID": f"QID{question_id}"
        }
    }

    return matrix_block

def create_qsf_likert(survey_content, TOPIC):

    bot_message = "Without making content changes, adapt the following list of statements to the following format, including quotations and separated by commas: \"I feel valued at work\", \"I have the resources I need\", \"My workload is manageable\"" + survey_content

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    s = str(response.text)
    
    likert_q = create_likert_matrix_question_block(
    question_id=4,
    label=TOPIC,
    question_text="Please rate how much you agree with each statement:",
    statements = [part.strip().strip('"') for part in s.split('", "')],
    scale_options=[
        "Strongly Disagree", "Disagree", "Neutral",
        "Agree", "Strongly Agree"
    ],
    single_answer=True  # one response per row
    )

    questions = [likert_q]
    create_qsf_file(questions, output_filename="qsf_files/generated_survey.qsf")


def create_qsf_mc(survey_content):
    
    bot_message = "Without making content changes, adapt the following survey to the following format (all features of the survey, including questions, are separated by pipe characters) of this example 3-question survey: '1|age|How old are you?|Under 18, 18-24, 25-34 | 2|favorite_fruit|Which of the following is your favorite fruit?|Apple, Banana, Orange, Strawberry | 3|transportation_mode|What is your primary mode of transportation?|Car, Bus, Train, Bike, Walk. |' The output will be structured to feed into a computer program, so do not add any additional text. Here's the survey: " + survey_content

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    input_str = str(response.text)
    input_str = input_str[input_str.find("1|"):]

    question_counter, questions = create_short_survey_from_string(input_str)

    generated_qsf_path = "qsf_files/generated_survey.qsf"
    create_qsf_file(questions, survey_name="Auto Survey from Bot Message")


def upload_to_qualtrics(topic):
    '''
    Upload existing QSF to Qualtrics
    '''

    generated_qsf_path = "qsf_files/generated_survey.qsf"
    title = "Survey_" + topic.replace(" ", "_")

    # Endpoint for importing a QSF file
    import_url = f"{BASE_URL}/surveys"

    # Open the QSF file and post it to the API
    with open(generated_qsf_path, 'rb') as file:
        files = {
            'file': (generated_qsf_path, file, 'application/vnd.qualtrics.survey.qsf')
        }
        data = {"name": title}
        response = requests.post(import_url, headers=HEADERS, files=files, data=data)

    admin_url = ""
    preview_url = ""

    # Check the response
    if response.status_code == 200:
        return_code = 0 # survey imported correctly
        result = response.json()['result']
        survey_id = result['id']
        print(f"Survey imported successfully with ID: {survey_id}")

        # upenn qualtrics links
        admin_url = f"https://upenn.{DATA_CENTER}.qualtrics.com/Q/EditSection/Blocks/?SurveyID={survey_id}"
        preview_url = f"https://upenn.{DATA_CENTER}.qualtrics.com/jfe/preview/{survey_id}?Q_CHL=preview"
    else:
        print("Error importing survey:", response.text)

    return admin_url, preview_url

def simulate_single_response(survey_content, topic):
    '''
    Simulate one survey response
    '''
    
    bot_message = "Pretend you are about to take this survey on " + topic + ". Give us a brief description about yourself and then give your responses to the following survey: " + survey_content

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    filename = f"md_files/simulated_responses/{topic.replace(" ", "_")}_survey_response.md"

    # Save the response text
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response.text)

    return filename

def simulate_multiple_responses(survey_content, topic):
    '''
    Simulate multiple survey responses
    '''

    file_path = f"md_files/simulated_characters/{topic.replace(" ", "_")}_characters.md"
    with open(file_path, 'r', encoding='utf-8') as f:
        characters = f.read()
    
    bot_message = "Here is a survey about " + topic + "\n" + survey_content + "\n" ". Below, I have a list of characters that are to respond to the survey. For each character in the list, give the multiple-choice response AND a corresponding letter choice for each survey question, formatted nicely in a MD file. Only respond with the MD so that the response can be immediately used: " + characters

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    # Ensure the output folder exists
    os.makedirs("md_files/simulated_responses", exist_ok=True)

    # Create a safe filename
    filename = f"md_files/simulated_responses/{topic.replace(" ", "_")}_survey_responses_batch.md"

    # Save the response text
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response.text)

    return filename

def extract_data(survey_content, topic):

    # read survey responses
    filename = f"md_files/simulated_responses/{topic.replace(" ", "_")}_survey_responses_batch.md"
    with open(filename, 'r', encoding='utf-8') as f:
        survey_simulations = f.read()

    # write extractable survey info
    bot_message = "Here is a survey: " + survey_content + "\nRespond only with text that can be fed into a function, representing the survey using the following format: "
    bot_message += "1 Insert First Question Text; a. Option 1; b. Option 2; c. Option 3 | 2 Insert Second Question Text; a. Option 1; b. Option 2; c. Option 3 |"

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    # Ensure the output folder exists
    os.makedirs("survey_data", exist_ok=True)

    filename = f"survey_data/survey.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response.text)

    # write extractable response info
    bot_message = "Here are the results of survey: " + survey_simulations + "\nRespond only with text that can be fed into a function, representing each respondent's answers in the following format: "
    bot_message += "a,b,b,c,b | b,a,a,a,c | c,b,a,d,a |"

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    filename = f"survey_data/responses.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response.text)

def create_character_list(survey_content, topic, num):
    '''
    Create and return a list of characters to simulate survey responses
    '''

    bot_message = "Copied below is a survey on " + topic + ". Come up with " + str(num) + " characters to take the survey. For now, for each character, give a quick description, including their name, age, nation of origin, demographic information. Respond only with the character list as your response will feed into text output." + survey_content

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    # Ensure the output folder exists
    os.makedirs("md_files/simulated_characters", exist_ok=True)

    # Create a safe filename
    filename = f"md_files/simulated_characters/{topic.replace(" ", "_")}_characters.md"

    # Save the response text
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response.text)

    return filename

def revise_character_list(revision, topic):
    '''
    Make any changes to list of simulated characters
    '''

    file_path = f"md_files/simulated_characters/{topic.replace(" ", "_")}_characters.md"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    bot_message = "Copied below is a list of made-up respondent profiles for a survey about " + topic + "\n" + content + "\n" ". Revise the list of profiles based on the following feedback. Respond only with the character list as your response will feed into text output: " + revision

    response = CLIENT.models.generate_content(
        model="gemini-2.0-flash", contents=bot_message
    )

    # Save the response text
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(response.text)

    return file_path
