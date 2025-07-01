"""
Small helper script to download nltk libraries.
"""

import ssl

import nltk


def download():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    nltk.download("vader_lexicon")
    nltk.download("wordnet")


if __name__ == "__main__":
    download()
