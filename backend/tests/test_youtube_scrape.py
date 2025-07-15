"""
Test the youtube_scrape module
"""

import json
import re
from typing import Optional
from unittest.mock import MagicMock, patch

from backend.src.youtube_scrape import (
    extract_channel_data,
    extract_comment_thread_data,
    extract_search_data,
    fuzzy_similarity,
    main,
    perform_sentiment_analysis,
    transform_channel_data,
    transform_comment_thread_data,
    transform_data,
)


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

    str2 = (
        "DodgerBlue.com is run by credentialed reporters and your "
        + "trusted source for the latest Los Angeles Dodgers news, rumors, "
        + "opinion, score updates and more involving Shohei Ohtani, Mookie"
        + " Betts, Freddie Freeman"
    )
    result = fuzzy_similarity(str1, str2)
    assert result == 100.0

    str2 = (
        "Looking over the country with those sunken eyes as if the world"
        + " out there had been altered or made suspect by what he’d seen of it "
        + "elsewhere. As if he might never see it right again. Or worse did "
        + "see it right at last. See it as it had always been, would "
        "forever be."
    )
    result = fuzzy_similarity(str1, str2)
    assert result == 55.0


def test_perform_sentiment_analysis():
    """
    Test the perform_sentiment_analysis method.
    """

    str1 = (
        "Looking over the country with those sunken eyes as if the world"
        + " out there had been altered or made suspect by what he’d seen of it "
        + "elsewhere. As if he might never see it right again. Or worse "
        + "did see it right at last. See it as it had always been, would "
        + "forever be."
    )
    result = perform_sentiment_analysis(str1)
    assert result == 0.0

    str1 = "Good!, Great!, Fantastic!"
    result = perform_sentiment_analysis(str1)
    assert result == 0.691

    str1 = "Terrible!, Horrible!, Sucks!"
    result = perform_sentiment_analysis(str1)
    assert result == 0.0

    str1 = (
        "The shoe is on the hand it fits, there's really nothing much to it "
        + "Whistle through your teeth and spit 'cause it's alright "
        + "Oh, well, a touch of grey, kinda suits you anyway "
        + "That was all I had to say and it's alright"
    )
    result = perform_sentiment_analysis(str1)
    assert result == 0.226


@patch("bonobo.config.use")
def test_transform_channel_data(use_mock: MagicMock):
    """
    Test the transform_channel_data method.
    """
    columns = [
        "Channel_Id",
        "Title",
        "Url",
        "Description",
        "Videos",
        "Subscribers",
        "Similarity",
    ]

    use_mock.return_value = None
    with open("backend/tests/channel_results.json", "r") as json_file:
        channel_data = json.load(json_file)
    key, df = next(transform_channel_data(channel_data, "dodgers"))
    assert key == "channel_data"
    assert df.columns.to_list() == columns
    assert len(df) == 30
    assert all(
        [
            similarity >= 0.0 and similarity <= 100.0
            for similarity in df["Similarity"].to_list()
        ]
    )
    assert all(
        [
            re.match("https://www.youtube.com/.*", url)
            for url in df["Url"].to_list()
        ]
    )


@patch("bonobo.config.use")
def test_transform_comment_thread_data(use_mock: MagicMock):
    """
    Test the transform_comment_thread_data method.
    """
    columns = [
        "Channel_Id",
        "Score",
    ]
    use_mock.return_value = None
    with open("backend/tests/comment_thread_results.json", "r") as json_file:
        comment_threads_data = json.load(json_file)
    key, df = next(transform_comment_thread_data(comment_threads_data))
    assert key == "comment_thread_data"
    assert df.columns.to_list() == columns
    assert len(df) == 3
    assert all(
        [score >= 0.0 and score <= 1.0 for score in df["Score"].to_list()]
    )


@patch("bonobo.config.use")
def test_transform_data(use_mock: MagicMock):
    """
    Test the transform_data method.
    """
    columns = [
        "Channel_Id",
        "Title",
        "Url",
        "Description",
        "Videos",
        "Subscribers",
        "Similarity",
        "Score",
        "Videos_Rank",
        "Subscribers_Rank",
        "Score_Rank",
        "Similarity_Rank",
        "Average_Rank",
    ]
    use_mock.return_value = None

    with open("backend/tests/comment_thread_results.json", "r") as json_file:
        comment_thread_data = json.load(json_file)

    with open("backend/tests/channel_results.json", "r") as json_file:
        channel_data = json.load(json_file)

    _, comment_thread_df = next(
        transform_comment_thread_data(comment_thread_data)
    )
    _, channel_data_df = next(transform_channel_data(channel_data, "dodgers"))

    kv_store_mock = {
        "channel_data": channel_data_df,
        "comment_thread_data": comment_thread_df,
    }
    with patch("backend.src.youtube_scrape.KV_STORE", kv_store_mock):
        df = transform_data()

    assert len(df) == 2
    assert all(
        [score >= 0.0 and score <= 1.0 for score in df["Score"].to_list()]
    )

    assert all(
        [
            similarity >= 0.0 and similarity <= 100.0
            for similarity in df["Similarity"].to_list()
        ]
    )

    assert all(
        [rank > 0 and rank <= len(df) for rank in df["Videos_Rank"].to_list()]
    )

    assert all(
        [
            rank > 0 and rank <= len(df)
            for rank in df["Subscribers_Rank"].to_list()
        ]
    )

    assert all(
        [rank > 0 and rank <= len(df) for rank in df["Score_Rank"].to_list()]
    )

    assert df.columns.to_list() == columns


@patch("googleapiclient.discovery.build")
def test_extract_comment_thread_data(mock_googleapi: MagicMock):
    """
    Tests the extract_comment_thread_data method.
    """

    def list_method(part: Optional[str], videoId: Optional[str]):
        video_id = str(videoId)
        assert part == "id, replies, snippet"
        retval = MagicMock()
        retval.execute.return_value = {"videoId": video_id}
        return retval

    instance = MagicMock()
    comment_threads = MagicMock()
    comment_threads.list.side_effect = list_method
    instance.commentThreads.return_value = comment_threads
    mock_googleapi.return_value = instance

    with open("backend/tests/search_results.json", "r") as json_file:
        search_data = json.load(json_file)

    search_data_results = []
    for list_item in search_data:
        for item in list_item.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            channel_id = item.get("snippet", {}).get("channelId")
            search_data_results.append((video_id, channel_id))

    comment_thread_data = next(extract_comment_thread_data(search_data_results))
    assert comment_threads.list.call_count == 23

    search_data_l = []
    for list_item in search_data:
        for item in list_item.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            search_data_l.append(video_id)

    for list_item in comment_thread_data.get("items", []):
        for video_id in [
            item["videoId"] for item in list_item.get("items", [])
        ]:
            assert video_id in search_data_l


@patch("googleapiclient.discovery.build")
def test_extract_channel_data(mock_googleapi: MagicMock):
    """
    Tests the extract_channel_data method.
    """

    def list_method(
        part: Optional[str] = None,
        id: Optional[str] = None,
        pageToken: Optional[str] = None,
        maxResults: int = 5,
    ):
        id = str(id)
        assert part == "id, statistics, snippet"
        ids = id.split(",")
        assert len(ids) <= 10
        retval = MagicMock()
        retval.id.return_value = {"id": id}
        retval.execute.return_value = {"items": [{"id": id} for id in ids]}
        return retval

    instance = MagicMock()
    channels = MagicMock()
    channels.list.side_effect = list_method
    instance.channels.return_value = channels
    mock_googleapi.return_value = instance

    with open("backend/tests/search_results.json", "r") as json_file:
        search_data = json.load(json_file)

    search_data_results = []
    for list_item in search_data:
        for item in list_item.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            channel_id = item.get("snippet", {}).get("channelId")
            search_data_results.append((video_id, channel_id))

    result = next(extract_channel_data(search_data_results))
    assert channels.list.call_count == 2
    assert "items" in result
    items = result.get("items", [])
    assert len(items) == 17
    for item in items:
        assert "id" in item

    search_data_l = []
    for list_item in search_data:
        for item in list_item.get("items", []):
            channel_id = item.get("snippet", {}).get("channelId")
            search_data_l.append(channel_id)

    for list_item in result.get("items", []):
        list_item.get("id") in search_data_l


@patch("googleapiclient.discovery.build")
def test_extract_channel_data_with_page_token(mock_googleapi: MagicMock):
    """
    Tests the extract_channel_data method with paging.
    """

    def list_method(
        part: Optional[str] = None,
        id: Optional[str] = None,
        pageToken: Optional[str] = None,
        maxResults: int = 5,
    ):
        _ = maxResults
        id = str(id)
        assert part == "id, statistics, snippet"
        ids = id.split(",")
        assert len(ids) <= 10
        retval = MagicMock()
        retval.id.return_value = {"id": id}
        if not pageToken:
            retval.execute.return_value = {
                "nextPageToken": "foobar",
                "items": [{"id": id} for id in ids],
            }
        else:
            retval.execute.return_value = {"items": [{"id": id} for id in ids]}
        return retval

    instance = MagicMock()
    channels = MagicMock()
    channels.list.side_effect = list_method
    instance.channels.return_value = channels
    mock_googleapi.return_value = instance

    with open("backend/tests/search_results.json", "r") as json_file:
        search_data = json.load(json_file)

    search_data_results = []
    for list_item in search_data:
        for item in list_item.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            channel_id = item.get("snippet", {}).get("channelId")
            search_data_results.append((video_id, channel_id))

    result = next(extract_channel_data(search_data_results))
    assert channels.list.call_count == 4
    assert "items" in result
    items = result.get("items", [])
    assert len(items) == 34
    for item in items:
        assert "id" in item

    search_data_l = []
    for list_item in search_data:
        for item in list_item.get("items", []):
            channel_id = item.get("snippet", {}).get("channelId")
            search_data_l.append(channel_id)

    for list_item in result.get("items", []):
        list_item.get("id") in search_data_l


@patch("googleapiclient.discovery.build")
@patch("bonobo.config.use")
def test_extract_search_data_with_page_token(
    mock_use: MagicMock, mock_googleapi: MagicMock
):
    """
    Tests the extract_channel_data method with paging.
    """

    def list_method(
        part: Optional[str] = None,
        q: Optional[str] = None,
        pageToken: Optional[str] = None,
        maxResults: int = 5,
        safeSearch: Optional[str] = None,
    ):
        _ = q
        assert part == "snippet"
        retval = MagicMock()
        with open("backend/tests/search_results.json", "r") as json_file:
            search_data = json.load(json_file)
        if not pageToken:
            retval.execute.return_value = search_data[0]
        else:
            ret_dict = search_data[0]
            del ret_dict["nextPageToken"]
            retval.execute.return_value = ret_dict
        return retval

    mock_use.return_value = None
    instance = MagicMock()
    search = MagicMock()
    search.list.side_effect = list_method
    instance.search.return_value = search
    mock_googleapi.return_value = instance

    result = next(extract_search_data("dodgers"))
    assert instance.search.call_count == 2
    assert len(result) == 100


@patch("backend.src.youtube_scrape.extract_search_data")
@patch("backend.src.youtube_scrape.extract_channel_data")
@patch("backend.src.youtube_scrape.extract_comment_thread_data")
@patch("backend.src.download.download")
@patch("googleapiclient.discovery.build")
@patch("bonobo.run")
@patch("bonobo.Graph")
def test_main(
    mock_graph: MagicMock,
    mock_run: MagicMock,
    mock_googleapiclient: MagicMock,
    mock_download: MagicMock,
    mock_extract_comment_thread_data: MagicMock,
    mock_extract_channel_data: MagicMock,
    mock_extract_search_data: MagicMock,
):
    """
    Test the main method.

    Parameters
    ----------
    mock_googleapiclient : MagicMock
        Mock for googleapi
    mock_download : MagicMock
        Mock for NLTK downloads
    mock_extract_comment_thread_data : MagicMock
        Mock for comment thread data download
    mock_extract_channel_data : MagicMock
        Mock for channel data download
    mock_extract_search_data : MagicMock
        Mock for search data download
    """
    columns = [
        "Channel_Id",
        "Title",
        "Url",
        "Description",
        "" "Videos",
        "Subscribers",
        "Similarity",
        "Score",
        "Videos_Rank",
        "Subscribers_Rank",
        "Score_Rank",
        "Similarity_Rank",
        "Average_Rank",
    ]
    with open("backend/tests/search_results.json", "r") as json_file:
        search_data = json.load(json_file)
    with open("backend/tests/channel_results.json", "r") as json_file:
        channel_data = json.load(json_file)
    with open("backend/tests/comment_thread_results.json", "r") as json_file:
        comment_thread_data = json.load(json_file)

    mock_extract_comment_thread_data.return_value = comment_thread_data
    mock_extract_channel_data.return_value = channel_data
    mock_extract_search_data.return_value = search_data
    mock_download.return_value = None
    mock_googleapiclient.return_value = MagicMock()
    mock_run.return_value = None
    mock_graph.add_chain.return_value = None
    _, comment_thread_df = next(
        transform_comment_thread_data(comment_thread_data)
    )
    _, channel_data_df = next(transform_channel_data(channel_data, "dodgers"))

    kv_store_mock = {
        "channel_data": channel_data_df,
        "comment_thread_data": comment_thread_df,
    }
    with patch("backend.src.youtube_scrape.KV_STORE", kv_store_mock):
        df = main("dodgers")
        assert len(df) == 2
        assert all(
            [score >= 0.0 and score <= 1.0 for score in df["Score"].to_list()]
        )

        assert all(
            [
                similarity >= 0.0 and similarity <= 100.0
                for similarity in df["Similarity"].to_list()
            ]
        )

        assert all(
            [
                rank > 0 and rank <= len(df)
                for rank in df["Videos_Rank"].to_list()
            ]
        )

        assert all(
            [
                rank > 0 and rank <= len(df)
                for rank in df["Subscribers_Rank"].to_list()
            ]
        )

        assert all(
            [
                rank > 0 and rank <= len(df)
                for rank in df["Score_Rank"].to_list()
            ]
        )

        assert df.columns.to_list() == columns
