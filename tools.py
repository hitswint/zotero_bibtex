# -*- coding: utf-8 -*-
#
import string
import random
import enchant
from titlecase import titlecase


def translate_month(key):
    """The month value can take weird forms. Sometimes, it's given as an int,
    sometimes as a string representing an int, and sometimes the name of the
    month is spelled out. Try to handle most of this here.
    """
    months = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]

    # Sometimes, the key is just a month
    try:
        return months[int(key) - 1]
    except (TypeError, ValueError):
        # TypeError: unsupported operand type(s) for -: 'str' and 'int'
        pass

    # Split for entries like "March-April"
    strings = []
    for k in key.split("-"):
        month = k[:3].lower()

        # Month values like '????' appear -- skip them
        if month in months:
            strings.append(month)
        else:
            print("Unknown month value '{}'. Skipping.".format(key))
            return None

    return ' # "-" # '.join(strings)


def create_dict():
    d = enchant.DictWithPWL("en_US")
    return d


def _translate_word(word, d):
    # Check if the word needs to be protected by curly braces to prevent
    # recapitalization.
    if not word:
        needs_protection = False
    elif word.count("{") != word.count("}"):
        needs_protection = False
    elif word[0] == "{" and word[-1] == "}":
        needs_protection = False
    elif any([char.isupper() for char in word[1:]]):
        needs_protection = True
    else:
        needs_protection = (any([char.isupper() for char in word])
                            and d.check(word) and not d.check(word.lower()))

    if needs_protection:
        return "{" + word + "}"
    return word


def _translate_title(val, dictionary=create_dict()):
    """The capitalization of BibTeX entries is handled by the style, so names
    (Newton) or abbreviations (GMRES) may not be capitalized. This is unless
    they are wrapped in curly braces.
    This function takes a raw title string as input and {}-protects those parts
    whose capitalization should not change.
    """
    # If the title is completely capitalized, it's probably by mistake.
    if val == val.upper():
        val = val.title()

    words = val.split()
    # Handle colons as in
    # ```
    # Algorithm 694: {A} collection...
    # ```
    for k in range(len(words)):
        if k > 0 and words[k - 1][-1] == ":" and words[k][0] != "{":
            words[k] = "{" + words[k].capitalize() + "}"

    words = [
        "-".join([_translate_word(w, dictionary) for w in word.split("-")])
        for word in words
    ]

    oldtitle = " ".join(words)

    # Apply titlecase to get the correct title.
    newtitle = titlecase(oldtitle)

    return newtitle


def convert_to_bibtex_string(
        entry,
        bibtex_key,
        brace_delimeters=True,
        tab_indent=False,
        dictionary=create_dict(),
        sort=False,
):
    """String representation of BibTeX entry.
    """
    indent = "\t" if tab_indent else " "
    out = "@{}{{{},\n{}".format(entry["itemType"], bibtex_key, indent)
    content = []

    left, right = ["{", "}"] if brace_delimeters else ['"', '"']

    keys = entry.keys()
    if sort:
        keys = sorted(keys)

    for key in keys:
        if key.lower() in [
                "id",
                "notes",
                "itemtype",
                "accessdate",
                "seealso",
                "attachments",
                "url",
                "journalabbreviation",
        ]:
            continue

        value = entry[key]

        # Remove once <https://github.com/mcmtroffaes/latexcodec/issues/56> is
        # *released*.
        try:
            value = value.replace("\u2010", "-")
        except AttributeError:
            pass

        # Always make keys lowercase
        key = key.lower()

        if key == "month":
            month_string = translate_month(value)
            if month_string:
                content.append("{} = {}".format(key, month_string))
        elif key == "title":
            content.append(u"{} = {}{}{}".format(
                key, left, _translate_title(value, dictionary), right))
        else:
            if value is not None:
                content.append(u"{} = {}{}{}".format(key, left, value, right))

    # Make sure that every line ends with a comma
    out += indent.join([line + ",\n" for line in content])
    out += "}"
    return out


def write(od, file_path, delimeter_type, tab_indent):
    # Create the dictionary only once
    dictionary = create_dict()

    # Write header to the output file.
    segments = []

    brace_delimeters = delimeter_type == "braces"

    # Add segments for each bibtex entry in order
    segments.extend([
        convert_to_bibtex_string(
            d,
            "".join(
                random.choice(string.ascii_uppercase + string.digits)
                for _ in range(6)),
            brace_delimeters=brace_delimeters,
            tab_indent=tab_indent,
            dictionary=dictionary,
            sort=True) for d in od
    ])

    with open(file_path, 'a') as f:
        # data = f.read()
        f.write("\n\n".join(segments) + "\n")
