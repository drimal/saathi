import re
import inflect

p = inflect.engine()


def clean_text_for_tts(text):
    # Convert to lowercase (optional, depending on TTS engine behavior)
    sanitized_text = text  # .lower()
    # Use a regex pattern to match any text between triple backticks
    # sanitized_text = re.sub(r"```.*?```", "", text, flags=re.DOTALL).strip()

    # Remove unnecessary special characters (except for essential punctuation)
    sanitized_text = re.sub(r"[^\w\s,.!?]", "", sanitized_text)

    # Expand contractions
    contractions = {
        "can't": "cannot",
        "won't": "will not",
        "i'm": "i am",
        "it's": "it is",
        "he's": "he is",
        "she's": "she is",
        "we're": "we are",
        "they're": "they are",
        "i've": "i have",
        "you've": "you have",
        "we've": "we have",
        "they've": "they have",
        "isn't": "is not",
        "aren't": "are not",
        "wasn't": "was not",
        "weren't": "were not",
        "doesn't": "does not",
        "don't": "do not",
        "didn't": "did not",
        "hasn't": "has not",
        "haven't": "have not",
        "hadn't": "had not",
        "shouldn't": "should not",
        "wouldn't": "would not",
        "couldn't": "could not",
        "mustn't": "must not",
        "let's": "let us",
        "that's": "that is",
        "there's": "there is",
        "what's": "what is",
        "who's": "who is",
        "here's": "here is",
        "where's": "where is",
        "how's": "how is",
    }

    for contraction, expansion in contractions.items():
        sanitized_text = re.sub(r"\b" + contraction + r"\b", expansion, sanitized_text)

    # Expand common abbreviations
    abbreviations = {
        "dr.": "doctor",
        "mr.": "mister",
        "mrs.": "missus",
        "ms.": "miss",
        "st.": "saint",
        "vs.": "versus",
        "etc.": "et cetera",
        "e.g.": "for example",
        "i.e.": "that is",
        " & ": " and ",
        " % ": " percent ",
        " @ ": " at ",
        " = ": " equals ",
        " + ": " plus ",
        " / ": " slash ",
    }

    for abbr, full_form in abbreviations.items():
        sanitized_text = re.sub(r"\b" + abbr + r"\b", full_form, sanitized_text)

    # Convert numbers to words (handle both digit-based and written numbers)
    def replace_numbers(match):
        number = match.group()
        return p.number_to_words(number)

    sanitized_text = re.sub(r"\b\d+\b", replace_numbers, sanitized_text)

    # Ensure proper pauses by replacing commas with periods for stronger pauses
    sanitized_text = sanitized_text.replace(",", ".")

    return sanitized_text
