# Welcome to AutoScience — your AI-powered survey assistant for Discord!

AutoScience can help you:

- Create surveys
- Revise them
- Export them as .md or .qsf files
- Simulate survey responses
- Upload to Qualtrics


# Configure Environment

You will need the following to correctly run AutoScience: 

- Discord Token (bot runs primarily in Discord)
- Gemini API Key (to generate surveys)
- Qualtrics Token (to automate survey uploads Qualtrics, optional)

To run: ```python bot.py```

# Project Directory

AutoScience/
├─ bot.py                # Discord bot (primary entry point into program)
├─ create_survey.py      # LLM prompts + Qualtrics helpers
├─ display_data.py       # Matplotlib / report generation
├─ help.md               # In‑chat help (also served to users)
├─ README.md             # <–– you are here
└─ (additional folders)  # Store intermediate and resulting files 

