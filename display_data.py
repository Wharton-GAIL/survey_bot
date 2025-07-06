import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import textwrap

def parse_survey(filename):

    with open(filename, 'r') as f:
        raw = f.read().strip()

    questions = []
    for q_raw in raw.split(' | '):
        parts = q_raw.split(';')
        q_text = parts[0].strip()
        choices = [opt.strip().split('. ', 1)[1] for opt in parts[1:]]
        questions.append((q_text, choices))
    return questions

def parse_responses(filename):
    with open(filename, 'r') as f:
        raw = f.read().strip()

    response_lines = [line.strip().split(',') for line in raw.split(' | ')]
    return response_lines

def tally_responses(questions, response_lines):
    tally = [dict() for _ in questions]
    for line in response_lines:
        for i, response in enumerate(line):
            tally[i][response] = tally[i].get(response, 0) + 1
    return tally

def generate_pdf_report(questions, tally):

    filename="survey_data/report.pdf"

    with PdfPages(filename) as pdf:
        for i, ((q_text, choices), response_counts) in enumerate(zip(questions, tally)):
            labels = [chr(ord('a') + j) for j in range(len(choices))]
            counts = [response_counts.get(l, 0) for l in labels]

            # Wrap long labels
            wrapped_choices = ['\n'.join(textwrap.wrap(choice, width=30)) for choice in choices]

            # Create a letter-sized page
            fig, ax = plt.subplots(figsize=(8.5, 11))  # US letter

            # Plot the bar chart
            ax.bar(wrapped_choices, counts)
            ax.set_title(f"Q{i+1}: {q_text}", fontsize=13, wrap=True, pad=20)
            ax.set_ylabel("Number of Responses", fontsize=11)
            ax.tick_params(axis='x', labelrotation=30, labelsize=11)
            ax.tick_params(axis='y', labelsize=11)

            # Adjust layout: occupy top half of the page
            plt.subplots_adjust(
                top=0.85,     # raise top of the chart
                bottom=0.55,  # raise bottom margin (move chart up)
                left=0.15,
                right=0.9
            )

            pdf.savefig(fig)
            plt.close()

# Entrypoint 
def process_data():

    survey_file = "survey_data/survey.md"
    responses_file = "survey_data/responses.md"

    questions = parse_survey(survey_file)
    responses = parse_responses(responses_file)
    tally = tally_responses(questions, responses)
    generate_pdf_report(questions, tally)