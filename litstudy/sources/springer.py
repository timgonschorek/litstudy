import csv
from typing import Dict, Union

import pandas as pd
from ..types import Document, Author, DocumentSet, DocumentIdentifier, Affiliation
from ..common import robust_open
import logging

from pandas import DataFrame


class SpringerDocument(Document):
    def __init__(self, entry):
        doi = entry.get("Item DOI") or None
        title = entry.get("Item Title")

        super().__init__(DocumentIdentifier(title, doi=doi))
        self.entry = entry

    @property
    def title(self) -> str:
        return self.entry["Item Title"]

    @property
    def authors(self):
        if isinstance(self.entry, dict):
            authors = extract_author_names(self.entry.get("Authors"))
            affs = self.entry.get("Author Affiliations", "").split("; ")

            # Bug fix #55:
            # In some cases, the number of affiliations does not match the number of authors
            # given by the CSV file. Since there is no way of knowing which affiliations belong
            # to which authors, we just ignore all affiliations in this case.
            if len(authors) != len(affs):
                logging.warn(
                    (
                        f"affiliations for entry '{self.title}' are invalid: the number of authors "
                        f"({len(authors)}) does not match the number of author affilications ({len(affs)})"
                    )
                )

                affs = [None] * len(authors)

            return [SpringerAuthor(a.strip(), b) for a, b in zip(authors, affs)]

        elif isinstance(self.entry, pd.DataFrame):
            authors = [SpringerAuthor(n, a) for n, a in zip(self.entry["Authors"].split("; "), [])]
            return authors

    @property
    def publisher(self):
        return "springer"

    @property
    def publication_year(self):
        try:
            return int(self.entry["Publication Year"])
        except Exception:
            return None


class SpringerAffiliation(Affiliation):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


class SpringerAuthor(Author):
    def __init__(self, name, affiliation):
        self._name = name
        self._affiliation = affiliation

    @property
    def name(self):
        return self._name

    @property
    def affiliations(self):
        # Handle special case where affiliation is NA (not applicable)
        if not self._affiliation or self._affiliation == "NA":
            return None

        return [SpringerAffiliation(self._affiliation)]


def extract_author_names(author_string) -> list[str]:
    """
  Extracts author names from a string where names are concatenated.

  Args:
    author_string: A string containing author names without delimiters.

  Returns:
    A list of extracted author names.
  """

    names = []
    current_name = ""
    for i, char in enumerate(author_string):
        if char.isupper() and i > 1 and author_string[i - 1].islower():
            current_name_split = current_name.split(' ')
            if len(current_name_split) > 1:
                try:
                    names.append(f"{current_name_split[-1]}, {current_name_split[0][0]}.")
                except IndexError as err:
                    print(f"Error: {err}")
                    print(f"Current name: {current_name_split}")
            else:
                names.append(current_name)

            current_name = char
        else:
            current_name += char
    # Append the last name
    current_name_split = current_name.split(' ')
    if len(current_name_split) > 1:
        try:
            names.append(f"{current_name_split[-1]}, {current_name_split[0][0]}.")
        except IndexError as err:
            print(f"Error: {err}")
            print(f"Current name: {current_name_split}")
    else:
        names.append(current_name)
    return names


def load_springer_csv(path: str) -> DocumentSet:
    """Load CSV file exported from
    `Springer Link <https://link.springer.com/>`_.
    """
    with robust_open(path) as f:
        lines = csv.DictReader(f)
        docs = [SpringerDocument(line) for line in lines]
        return DocumentSet(docs)
