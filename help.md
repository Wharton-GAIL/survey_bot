Welcome to AutoScience — your AI-powered survey assistant for Discord!

AutoScience can help you:
• Create surveys
• Revise them
• Export them as .md or .qsf files
• Simulate survey responses
• Upload to Qualtrics

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

👩‍🔬 To Create a Survey:

Just type:
    autoscience, create a survey about [topic]

Example:
    autoscience, create a survey about public transportation in Philadelphia

AutoScience will first ask a few quick clarifying questions —including which format you prefer: (1) multiple‑choice or (2) Likert‑scale grid. After you answer, it will generate a draft survey and send it to you as a Markdown (.md) file.

🔁 To Revise the Survey:

After receiving the draft, simply reply with what you'd like changed.

Examples:
    Shorten the survey to five questions. 
    The questions should target students. 
    Remove question 3. 

When you're happy with the draft, respond with:
    ok

AutoScience will finalize it, save it to disk, and offer next steps (exporting, simulating responses, etc.).

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

📁 Exporting the Survey:
(The phrases in parentheses are not required for AutoScience to understand the command.)

Once a survey has been finalized, you can request the files:

• Get the Markdown (.md) version:
    autoscience, (send me the) md

• Get the QSF file (for importing into Qualtrics):
    autoscience, (send me the) qsf

• Get the PDF report (with question-response charts for visualization):
    autoscience, (send me the) report

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

🧪 Simulating Survey Responses:

AutoScience can simulate realistic survey responses from fictional characters.

To simulate a **single** random response:
    autoscience, simulate

To simulate **multiple** responses (e.g., 5):
    autoscience, simulate 5

For multiple responses:
1. AutoScience will first generate a character list with realistic traits.
2. You’ll receive a `.md` file previewing the character list.
3. You can revise this list by replying with changes.
    Example: "Make character 2 older" or "Add a high school student."
4. When ready, reply with:
    ok
5. AutoScience will simulate the full set of responses and send the results, along with a pdf report. 

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

📤 Upload to Qualtrics:

AutoScience can attempt to upload your most recent QSF survey to Qualtrics (the currently-integrated account) and return the preview and admin links. 

Command:
    autoscience, (upload the survey to) qualtrics

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

💡 Additional Commands:

• Check the topic of the most recent survey:
    autoscience, topic

• Ask for help:
    autoscience help

• Say hi (easter egg!):
    hello there

• Say thanks:
    autoscience thank you

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

🤖 More about AutoScience: 

AutoScience is an AI-powered Discord bot that streamlines the survey workflow for researchers. 
Features include co-creation of survey questions, QSF file generation, publishing to Qualtrics, and synthetic response generation for rapid piloting. By embedding survey design and response simulation directly into a chat environment, AutoScience accelerates survey development and deployment, lowering the barrier to rapid iteration and data-driven inquiry.