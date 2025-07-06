import os, random, tempfile, discord
from dotenv import load_dotenv

# See implementations of these functions in create_survey.py
from create_survey import (
    ideate_survey_mc, ideate_survey_likert, revise_survey,
    create_qsf_mc, create_qsf_likert, upload_to_qualtrics,
    simulate_single_response, simulate_multiple_responses,
    create_character_list, revise_character_list,
    extract_data, clarify_survey
)

from display_data import process_data

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# ────────────────────────────────────────────────
# Bot states
AWAITING_SURVEY   = False # Expecting user approval on survey draft
CLARIFYING_SURVEY = False # Expecting user to answer clarifying questions
AWAITING_SIM      = False # Expecting user approval on generated simulation characters 

CURR_SURVEY = "" # Store survey 
TOPIC       = "" # Store survey topic
LIKERT      = True # Likert format or MC format
# ────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

# ────────────────────────────────────────────────
def detect_action(content: str) -> str | None:
    """Return a symbolic label describing what the user just asked for."""
    lower = content.lower()

    if AWAITING_SURVEY:
        return 'SURVEY_OK' if 'ok' in lower else 'SURVEY_REV'

    if CLARIFYING_SURVEY:
        if any(k in lower for k in ('1', 'mc', 'multiple choice')):
            return 'CLARIFY_MC'
        if any(k in lower for k in ('2', 'grid', 'likert')):
            return 'CLARIFY_LIKERT'

    if AWAITING_SIM:
        return 'SIM_OK' if 'ok' in lower else 'SIM_REV'

    if lower == 'hello there':                                    return 'HELLO'
    if 'autoscience,' in lower and 'survey about' in lower:       return 'MAKE_SURVEY'
    if 'autoscience,' in lower and 'qsf'        in lower:         return 'GET_QSF'
    if 'autoscience,' in lower and 'report'     in lower:         return 'GET_REPORT'
    if 'autoscience,' in lower and 'md'         in lower:         return 'GET_MD'
    if 'autoscience,' in lower and 'simulate'   in lower:         return 'SIMULATE'
    if 'autoscience,' in lower and 'topic'      in lower:         return 'GET_TOPIC'
    if 'autoscience,' in lower and 'qualtrics'  in lower:         return 'UPLOAD_QSF'
    if 'autoscience'  in lower and 'thank'      in lower:         return 'THANKS'
    if lower == 'autoscience help':                                return 'HELP'
    if 'autoscience,' in lower:                                   return 'UNKNOWN'
    return None
# ────────────────────────────────────────────────

@client.event
async def on_message(message: discord.Message):
    global AWAITING_SURVEY, CLARIFYING_SURVEY, AWAITING_SIM
    global CURR_SURVEY, TOPIC, LIKERT

    if message.author == client.user:
        return

    action = detect_action(message.content)

    match action:
    # ───────── AWAITING SURVEY ──────────────────────────────
        case 'SURVEY_OK':
            AWAITING_SURVEY = False
            os.makedirs("md_files", exist_ok=True)
            file_path = os.path.join("md_files", "generated_survey.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(CURR_SURVEY)

            await message.channel.send(
                content=f"Here's the final survey about {TOPIC}.",
                file=discord.File(file_path)
            )
            await message.channel.send(
                "\nI can now...\n"
                "- Send the raw survey file (as MD or QSF)\n"
                "- Upload to your Qualtrics account\n"
                "- Simulate survey responses."
            )
            (create_qsf_likert if LIKERT else create_qsf_mc)(CURR_SURVEY, TOPIC)

        case 'SURVEY_REV':
            survey_response = revise_survey(CURR_SURVEY, message.content.lower())
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.md') as tmp:
                tmp.write(survey_response); tmp.seek(0)
                await message.channel.send(
                    content="Here's the revised survey.",
                    file=discord.File(tmp.name,
                                      filename=f"survey_{TOPIC.replace(' ', '_')}.md")
                )
            os.remove(tmp.name)
            CURR_SURVEY = survey_response
            await message.channel.send("Would you like any more changes? If not, reply 'ok'.")

    # ───────── CLARIFYING ─────────────────────────────────
        case 'CLARIFY_MC' | 'CLARIFY_LIKERT':
            LIKERT = (action == 'CLARIFY_LIKERT')
            func   = ideate_survey_likert if LIKERT else ideate_survey_mc
            survey_response = func(TOPIC, message.content.lower())

            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.md') as tmp:
                tmp.write(survey_response); tmp.seek(0)
                await message.channel.send(
                    content=f"Here's a preview of the survey about {TOPIC}.",
                    file=discord.File(tmp.name,
                                      filename=f"survey_{TOPIC.replace(' ', '_')}.md")
                )
            os.remove(tmp.name)

            await message.channel.send("Need tweaks? If not, reply 'ok'.")
            AWAITING_SURVEY, CURR_SURVEY, CLARIFYING_SURVEY = True, survey_response, False

    # ───────── AWAITING SIM CHARACTERS ────────────────────
        case 'SIM_OK':
            AWAITING_SIM = False
            await message.channel.send("Great. Simulating responses now...")
            outfile = simulate_multiple_responses(CURR_SURVEY, TOPIC)
            await message.channel.send(file=discord.File(outfile))

            extract_data(CURR_SURVEY, TOPIC)
            process_data()
            await message.channel.send(
                "Here's the final report:",
                file=discord.File("survey_data/report.pdf")
            )

        case 'SIM_REV':
            await message.channel.send("Here is the revised character list.")
            outfile = revise_character_list(message.content.lower(), TOPIC)
            await message.channel.send(file=discord.File(outfile))
            await message.channel.send("Further changes? If not, reply 'ok'.")

    # ───────── COMMANDS THAT SET/READ STATE ───────────────
        case 'MAKE_SURVEY':
            start = message.content.lower().find('survey about') + len('survey about')
            TOPIC = message.content[start:].strip()
            await message.channel.send(
                f"Hello, I'm AutoScience. Let me help you create a survey about {TOPIC}. "
                "Please give me a moment to think."
            )
            clarify_qs = clarify_survey(TOPIC) + \
                "\nAdditionally, would you like the survey format to be " \
                "(1) multiple choice or (2) likert-scale grid?"
            await message.channel.send(clarify_qs)
            CLARIFYING_SURVEY = True

        case 'GET_QSF':
            try:
                await message.channel.send(
                    "Here's the QSF file of the most recently-generated survey:",
                    file=discord.File('qsf_files/generated_survey.qsf')
                )
            except FileNotFoundError:
                await message.channel.send("Oops! I couldn't find the QSF file.")

        case 'GET_REPORT':
            try:
                await message.channel.send(
                    "Here's the report of the most recently-simulated survey:",
                    file=discord.File('survey_data/report.pdf')
                )
            except FileNotFoundError:
                await message.channel.send("Oops! I haven't simulated any surveys.")

        case 'GET_MD':
            try:
                await message.channel.send(
                    "Here's the MD file of the most recently-generated survey:",
                    file=discord.File('md_files/generated_survey.md')
                )
            except FileNotFoundError:
                await message.channel.send("Oops! I couldn't find the MD file.")

        case 'SIMULATE':
            await message.channel.send("One moment, generating survey response(s)...")
            parts  = message.content.lower().split()
            number = next((int(parts[i + 1]) for i, w in enumerate(parts)
                           if w == 'simulate' and i + 1 < len(parts)
                           and parts[i + 1].isdigit()), None)
            if number and number > 1:
                AWAITING_SIM = True
                await message.channel.send(
                    f"Compiling characters to simulate {number} survey responses."
                )
                outfile = create_character_list(CURR_SURVEY, TOPIC, number)
                await message.channel.send(file=discord.File(outfile))
                await message.channel.send(
                    "Would you like to edit the character list? If not, reply 'ok'."
                )
            else:
                await message.channel.send(
                    "Generating a character to simulate one survey response..."
                )
                outfile = simulate_single_response(CURR_SURVEY, TOPIC)
                await message.channel.send(file=discord.File(outfile))

        case 'GET_TOPIC':
            await message.channel.send(f"The topic of the most-recent survey is **{TOPIC}**.")

        case 'UPLOAD_QSF':
            await message.channel.send(
                "Uploading your most recently-created survey to Qualtrics..."
            )
            admin_url, preview_url = upload_to_qualtrics(TOPIC)
            if admin_url:
                await message.channel.send(
                    "Successfully imported into Qualtrics.\n"
                    f"Preview URL: {preview_url}\nAdmin URL: {admin_url}"
                )
            else:
                await message.channel.send("❌ There was an error importing into Qualtrics.")

    # ───────── GENERIC MISCELLANY ─────────────────────────
    
        case 'HELLO':
            await message.channel.send('General Kenobi')

        case 'THANKS':
            await message.channel.send("You're welcome, human.")

        case 'HELP':
            await message.channel.send(
                "I'm AutoScience, a bot that automates survey creation.\n"
                "Here's a full list of my abilities…"
            )
            await message.channel.send(file=discord.File('help.md'))

        case 'UNKNOWN':
            await message.channel.send("I'm sorry, I'm not sure how to do that.")

        case None:
            pass                                       # Non-bot chat – ignore silently
# ────────────────────────────────────────────────
client.run(TOKEN)
