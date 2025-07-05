"""
Test the youtube_scrape module
"""

import json
import re
from backend.src.youtube_scrape import fuzzy_similarity, perform_sentiment_analysis, transform_channel_data

def test_fuzzy_similarity():
    """
    Test the fuzzy_similarity method.
    """

    str1 = "Dodgers"
    str2 = "dodgers"
    result = fuzzy_similarity(str1, str2)
    assert result == 100.0

    result = fuzzy_similarity(str1, "")
    assert result == 0.0

    result = fuzzy_similarity(str1, "Dodge ball")
    assert result == 83.0

    str2 = ("DodgerBlue.com is run by credentialed reporters and your " +
    "trusted source for the latest Los Angeles Dodgers news, rumors, " + 
    "opinion, score updates and more involving Shohei Ohtani, Mookie" + 
    " Betts, Freddie Freeman")
    result = fuzzy_similarity(str1, str2)
    assert result == 100.0

    str2 = ("Looking over the country with those sunken eyes as if the world" +
    " out there had been altered or made suspect by what he’d seen of it " + 
    "elsewhere. As if he might never see it right again. Or worse did see " + 
    "it right at last. See it as it had always been, would forever be.")
    result = fuzzy_similarity(str1, str2)
    assert result == 55.0

def test_perform_sentiment_analysis():
    """
    Test the perform_sentiment_analysis method.
    """

    str1 = ("Looking over the country with those sunken eyes as if the world" +
    " out there had been altered or made suspect by what he’d seen of it " + 
    "elsewhere. As if he might never see it right again. Or worse did see " + 
    "it right at last. See it as it had always been, would forever be.")
    result = perform_sentiment_analysis(str1)
    assert result == 0.0

    str1 = "Good!, Great!, Fantastic!"
    result = perform_sentiment_analysis(str1)
    assert result == 0.691

    str1 = "Terrible!, Horrible!, Sucks!"
    result = perform_sentiment_analysis(str1)
    assert result == 0.0

    str1 = ("The shoe is on the hand it fits, there's really nothing much to it " +
    "Whistle through your teeth and spit 'cause it's alright " +
    "Oh, well, a touch of grey, kinda suits you anyway " +
    "That was all I had to say and it's alright")
    result = perform_sentiment_analysis(str1)
    assert result == 0.226

def test_transform_channel_data():
    """
    Test the transform_channel_data method.
    """
    columns = [
            "Channel Id",
            "Title",
            "Url",
            "Description",
            "Videos",
            "Subscribers",
            "Similarity"
        ]
    
    with open("backend/tests/channel_results.json", "r") as json_file:
        channel_data = json.load(json_file)
    df = transform_channel_data("dodgers", channel_data)
    assert df.columns.to_list() == columns
    assert len(df) == 15
    assert all([similarity >= 0.0 and similarity <= 100.0 for similarity in df["Similarity"].to_list()])
    assert all([re.match('https://www.youtube.com/.*', url) for url in df["Url"].to_list()])
