"""
support loading Scopus CSV export.
"""

from typing import List, Optional, Dict
import pandas as pd
from ..types import Document, Author, DocumentSet, DocumentIdentifier, Affiliation
from ..common import robust_open
import csv


class ScopusCsvAffiliation(Affiliation):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


class ScopusCsvAuthor(Author):
    def __init__(self, name, affiliation):
        self._name = name
        self._affiliation = affiliation

    @property
    def name(self):
        return self._name

    @property
    def affiliations(self):
        return [ScopusCsvAffiliation(self._affiliation)]


class ScopusCsvDocument(Document):
    def __init__(self, entry):
        doi = entry.get("DOI")
        title = entry.get("Title")
        pubmed_id = entry.get("PubMed ID")
        eid = entry.get("EID")
        identifier = DocumentIdentifier(title, doi=doi, pubmed=pubmed_id, eid=eid)
        super().__init__(identifier)
        self.entry = entry

    @property
    def title(self) -> Optional[str]:
        return self.entry.get("Title") or None

    @property
    def authors(self) -> List[ScopusCsvAuthor]:
        if isinstance(self.entry, dict):
            auths = self.entry.get("Authors")
            new_auths = auths.split(';')
            return [ScopusCsvAuthor(a.split('.')[0].strip(),'') for a in new_auths]
        elif isinstance(self.entry, pd.DataFrame):
            authors = [ScopusCsvAuthor(n, a) for n, a in zip(self.entry["Authors"].split("; "), [])]
            return authors
    @property
    def publisher(self) -> Optional[str]:
        return self.entry.get("Publisher") or None

    @property
    def publication_year(self) -> Optional[int]:
        year = self.entry.get("Year")
        if not year:
            return None

        try:
            return int(year)
        except:
            return None

    @property
    def keywords(self) -> Optional[List[str]]:
        keywords = self.entry.get("Author Keywords")
        if not keywords:
            return None
        return keywords.split("; ")

    @property
    def abstract(self) -> Optional[str]:
        abstract = self.entry.get("Abstract")
        if not abstract:
            return None
        return abstract

    @property
    def citation_count(self) -> Optional[int]:
        citation_count = self.entry.get("Cited by")
        if not citation_count:
            return None
        return int(citation_count)

    @property
    def language(self) -> Optional[str]:
        return self.entry.get("Language of Original Document") or None

    @property
    def publication_source(self) -> Optional[str]:
        return self.entry.get("Source title") or None

    @property
    def source_type(self) -> Optional[str]:
        return self.entry.get("Document Type") or None


def load_scopus_csv(path: str) -> DocumentSet:
    """Import CSV file exported from Scopus"""
    with robust_open(path) as f:
        lines = csv.DictReader(f)
        docs = [ScopusCsvDocument(line) for line in lines]
        return DocumentSet(docs)
