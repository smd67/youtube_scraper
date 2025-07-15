"""
API endpoint to search for YouTube videos, then make recommendations
for channels based on:

1. The number of videos
2. The number of subscribers
3. The positive sentiment of the comments of each video.
4. The similarity between the search term and a similar string in the channel
   description.

The output from the endpoint will be ranked by those criteria.
"""

import argparse
import os
import random
import re
from typing import Any, Generator

import bonobo
import googleapiclient.discovery
import pandas as pd
from bonobo.config import use
from download import download  # pylint: disable=import-error
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fuzzywuzzy import fuzz
from nltk.sentiment import SentimentIntensityAnalyzer
from pydantic import BaseModel

# from tabulate import tabulate

# Global data
KV_STORE: dict[str, pd.DataFrame] = (
    {}
)  # Key-Value storage for the transform results


class Query(BaseModel):
    """
    Pydantic representation of a query.
    """

    query_string: str


class Row(BaseModel):
    """
    A row of data returned by the backend.

    Parameters
    ----------
    Channel_Id : str
        The unique identifier for the recommended channel
    Title : str
        The title of the recommended channel
    Url : str
        The YouTube url for the recommended channel
    Description : str
        A description of the recommended channel
    Videos : int
        A count of videos that the recommended channel has
    Subscribers : int
        The number of subscribers that the ecommended channel has
    Similarity : float
        A value between 0 and 100 that indicates the similarity of the q
        string to the channel description
    Score : float
        A value between 0 and 1 that represents the percentage of favorable
        reviews for videos the channel hosts
    Videos_Rank : int
        The ranking position of the channel in regards to the number of videos
    Subscribers_Rank : int
        The ranking position of the channel in regards to the number of
        subscribers
    Score_Rank : int
        The ranking position of the channel in regards to the number of
        favorable comments
    Similarity_Rank : int
        The ranking position of the channel in regards to the similarity
        of the query string and description
    Average_Rank : float
        The average ranking of the channel based on all factors
    """

    Channel_Id: str
    Title: str
    Url: str
    Description: str
    Videos: int
    Subscribers: int
    Similarity: float
    Score: float
    Videos_Rank: int
    Subscribers_Rank: int
    Score_Rank: int
    Similarity_Rank: int
    Average_Rank: float


origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/query/")
def do_query(query: Query) -> list[Row]:
    """
    This is the main api entry point that the frontend communicates through.

    Parameters
    ----------
    query : Query
        This is the query string to search for. It gets used as the q parameter
        to the YouTube data API.


    Returns
    -------
    list[Row]
        A list of JSON objects that includes information about interesting
        channels you might want to subscribe to.
    """

    MAX_RESULTS = 20
    df = main(query.query_string).head(MAX_RESULTS)
    json_data = df.to_dict(orient="records")  # 'records' is a common format
    print("=================")
    print(json_data)
    print("=================")
    return [Row(**row_dict) for row_dict in json_data]


@use("query")
def extract_search_data(
    query: str,
) -> Generator[list[tuple[str, str]], None, None]:
    """
    Search for videos that match a query string.

    Parameters
    ----------
    query : str
        The query string used in the "q" parameter.

    Yields
    ------
    Generator[list[tuple[str, str]], None, None]
        A list of tuple pairs (video_id, channel_id)
    """
    MAX_RESULTS_PER_PAGE = 50
    MAX_PAGES = 5

    api_service_name = "youtube"
    api_version = "v3"
    api_key = os.environ.get("DEVELOPER_KEY")
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key
    )

    response_list: list[Any] = []
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": MAX_RESULTS_PER_PAGE,
        "safeSearch": "none",
    }
    while True:
        page_token = None

        if len(response_list) >= MAX_PAGES:
            break

        try:
            request = youtube.search().list(**params)  # type: ignore
            response = request.execute()
            response_list.append(response)
            page_token = response.get("nextPageToken")
        except googleapiclient.errors.HttpError as e:
            print(f"Error: unexpected exception e={e}")

        if page_token:
            params = {"part": "snippet", "q": query, "pageToken": page_token}
        else:
            break
    search_data = []
    for response in response_list:
        for item in response.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            channel_id = item.get("snippet", {}).get("channelId")
            search_data.append((video_id, channel_id))
    yield search_data


def extract_comment_thread_data(
    search_data: list[tuple[str, str]]
) -> Generator[dict[str, list[Any]], None, None]:
    """
    Extract comments for all of the videos.

    Parameters
    ----------
    search_data : list[tuple[str, str]]
        A list of tuple pairs (video_id, channel_id)

    Yields
    ------
    Generator[dict[str, list[Any]], None, None]
        Returs a dictionary with an "items" key whose value is the JSON data
        of all of the responses.
    """
    api_service_name = "youtube"
    api_version = "v3"
    api_key = os.environ.get("DEVELOPER_KEY")
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key
    )

    data: dict[str, list[Any]] = {}
    data["items"] = []
    videos: dict[str, list[Any]] = {}
    n = 2

    # Create dictionary
    for list_item in search_data:
        video_id = list_item[0]
        channel_id = list_item[1]
        if channel_id not in videos:
            videos[channel_id] = []
        videos[channel_id].append(video_id)

    for channel_id, video_list in videos.items():
        if len(video_list) > 2:
            video_list = random.sample(video_list, n)
        for video_id in video_list:
            try:
                request = youtube.commentThreads().list(  # type: ignore
                    part="id, replies, snippet", videoId=video_id
                )
                response = request.execute()
                data["items"].append(response)
            except googleapiclient.errors.HttpError:
                pass
    yield data


def extract_channel_data(
    search_data: list[tuple[str, str]]
) -> Generator[dict[str, list[Any]], None, None]:
    """
    Extract channel data for all of the videos.

    Parameters
    ----------
    search_data : list[tuple[str, str]]
        A list of tuple pairs (video_id, channel_id)

    Yields
    ------
    Generator[dict[str, list[Any]], None, None]
        Returns a dictionary with an "items" key whose value is the JSON data
        of all of the responses.
    """

    api_service_name = "youtube"
    api_version = "v3"
    api_key = os.environ.get("DEVELOPER_KEY")
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key
    )

    data: dict = {}
    data["items"] = []
    channel_ids = set()
    for list_item in search_data:
        channel_id = list_item[1]
        channel_ids.add(channel_id)

    channel_id_list = list(channel_ids)
    chunk_size = 10
    sublists = [
        channel_id_list[i : i + chunk_size]  # noqa: E203
        for i in range(0, len(channel_id_list), chunk_size)
    ]
    for sublist in sublists:
        channel_ids_str = ",".join(list(sublist))
        params = {
            "part": "id, statistics, snippet",
            "id": channel_ids_str,
            "maxResults": 50,
        }
        while True:
            page_token = None
            try:
                request = youtube.channels().list(**params)  # type: ignore
                response = request.execute()
                data["items"].extend(response.get("items", []))
                page_token = response.get("nextPageToken")
            except googleapiclient.errors.HttpError as e:
                print(f"Error: unexpected exception e={e}")

            if page_token:
                params = {
                    "part": "id, statistics, snippet",
                    "id": channel_ids_str,
                    "pageToken": page_token,
                }
            else:
                break
    yield data


def perform_sentiment_analysis(text: str) -> float:
    """
    Perform a sentiment analysis on each comment.

    Parameters
    ----------
    text : str
       The string to be analyzed.

    Returns
    -------
    float
        A value between 0.0 and 1.0 with 0.0 being no positive sentiment and
        1.0 being 100% positive sentiment.
    """
    # Initialize VADER sentiment analyzer
    sid = SentimentIntensityAnalyzer()

    # Perform sentiment analysis
    sentiment_score = sid.polarity_scores(text)["pos"]
    return sentiment_score


def transform_comment_thread_data(
    comment_thread_data: dict,
) -> Generator[tuple[str, pd.DataFrame], None, None]:
    """
    Transform the comment_thread_data into a useable dataframe.
    Parameters

    Parameters
    ----------
    comment_thread_data : dict
        A dictionary containing the comment thread data.

    Yields
    ------
    Generator[tuple[str, pd.DataFrame], None, None]
        A tuple pair (key, df) that contains the type of data and a
        useable dataframe.
    """

    print("in transform_comment_thread_data")
    data = []
    for item in comment_thread_data.get("items", []):
        for comment_item in item.get("items", []):
            channel_id = comment_item.get("snippet", {}).get("channelId", "")
            top_level = (
                comment_item.get("snippet", {})
                .get("topLevelComment", {})
                .get("snippet", {})
            )
            comment_text = top_level.get("textOriginal", "")
            score = perform_sentiment_analysis(comment_text)
            data.append((channel_id, score))
            for reply in comment_item.get("replies", {}).get("comments", []):
                comment_text = reply.get("snippet", {}).get("textOriginal", "")
                score = perform_sentiment_analysis(comment_text)
                data.append((channel_id, score))
    df = pd.DataFrame(data, columns=["Channel_Id", "Score"])
    grouped_data = df.groupby("Channel_Id")["Score"].mean()
    result_df = grouped_data.reset_index()
    yield ("comment_thread_data", result_df)


@use("query")
def transform_channel_data(
    channel_data: dict, query: str
) -> Generator[tuple[str, pd.DataFrame], None, None]:
    """
    Transform the channel_data into a useable dataframe.

    Parameters
    ----------
    channel_data : dict
        A dictionary containing the channel data.
    query : str
        A query string that maps to the q value in the youtube api.

    Yields
    ------
    Generator[tuple[str, pd.DataFrame], None, None]
        A tuple pair of (key, df) signifying the thype of data and a
        useable dataframe.
    """

    print("in transform_channel_data")
    data = []
    for channel_item in channel_data.get("items", []):
        channel_id = channel_item.get("id", "")
        custom_url = channel_item.get("snippet", {}).get("customUrl", "")
        url = f"https://www.youtube.com/{custom_url}"
        title = channel_item.get("snippet", {}).get("title", "")
        description = channel_item.get("snippet", {}).get("description", "")
        sim_score = fuzzy_similarity(query, f"{title} : {description}")
        video_count = channel_item.get("statistics", {}).get("videoCount", "")
        subscriber_count = channel_item.get("statistics", {}).get(
            "subscriberCount", ""
        )
        data.append(
            (
                channel_id,
                title,
                url,
                description,
                video_count,
                subscriber_count,
                sim_score,
            )
        )
    df = pd.DataFrame(
        data,
        columns=[
            "Channel_Id",
            "Title",
            "Url",
            "Description",
            "Videos",
            "Subscribers",
            "Similarity",
        ],
    )
    yield ("channel_data", df)


def transform_data() -> pd.DataFrame:
    """
    Tranforms the extracted data into a single dataframe.

    Parameters
    ----------
    query : str
        q parameter for the search data

    comment_thread_data : dict
        JSON dictionary containing comment thread results.

    channel_data : dict
        JSON dictionary containing channel results.

    Returns
    -------
    pd.DataFrame
        A combined dataframe with elements from the channel and comment threads.
    """

    comment_thread_df = KV_STORE["comment_thread_data"]

    channel_df = KV_STORE["channel_data"]

    combined_df = pd.merge(channel_df, comment_thread_df, on="Channel_Id")
    combined_df["Videos_Rank"] = combined_df["Videos"].rank(
        method="dense", ascending=False
    )
    combined_df["Subscribers_Rank"] = combined_df["Subscribers"].rank(
        method="dense", ascending=False
    )
    combined_df["Score_Rank"] = combined_df["Score"].rank(
        method="dense", ascending=False
    )
    combined_df["Similarity_Rank"] = combined_df["Similarity"].rank(
        method="dense", ascending=False
    )
    combined_df["Average_Rank"] = (
        combined_df["Videos_Rank"]
        + combined_df["Subscribers_Rank"]
        + combined_df["Score_Rank"]
        + combined_df["Similarity_Rank"]
    ) / 4.0

    combined_df = combined_df.sort_values(by="Average_Rank")

    return combined_df


def fuzzy_similarity(str1: str, str2: str) -> float:
    """
    Find the similarity between str1 and a match in str2 using a fuzzy
    comparison.

    Parameters
    ----------
    str1 : str
        This is the query string.
    str2 : str
        This is the description of the channel

    Returns
    -------
    int
        A ratio between 0 and 100 representing how similar the match is.
    """
    str1 = str1.lower()
    str2 = str2.lower()

    pattern_words = re.findall(r"\w+", str1)

    best_ratio = 0.0
    for i in range(len(str2)):
        text_words = re.findall(r"\w+", str2[i:])
        if len(text_words) < len(pattern_words):
            break
        ratios = [
            fuzz.ratio(w, text_words[j]) for j, w in enumerate(pattern_words)
        ]
        avg_ratio = sum(ratios) / len(ratios)
        if avg_ratio > best_ratio:
            best_ratio = avg_ratio

    return best_ratio


def get_services(query: str) -> dict[str, Any]:
    """
    Method used to pass global data and services into graph.

    Parameters
    ----------
    query : str
        The query string that is mapped to a q value in the youtube api call.

    Returns
    -------
    dict[str, Any]
        Returns a dictionary of services for a graph.
    """
    return {"query": query}


def store_results(key: str, df: pd.DataFrame):
    """
    Store transform results for final processing.

    Parameters
    ----------
    key : str
        The type of data (channel_data or comment_thread_data)
    df : pd.DataFrame
        The dataframe output by the transform function.
    """
    global KV_STORE
    KV_STORE[key] = df


def main(query: str):
    """
    Main method

    Parameters
    ----------
    query : str
        Query string or q parameter to search for.
    """

    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Download NLTK plug-ins
    download()

    # Create the Bonobo graph
    graph = bonobo.Graph()
    graph.add_chain(extract_search_data)
    graph.add_chain(store_results, _input=None)
    graph.add_chain(
        extract_channel_data,
        transform_channel_data,
        store_results,
        _input=extract_search_data,
    )
    graph.add_chain(
        extract_comment_thread_data,
        transform_comment_thread_data,
        store_results,
        _input=extract_search_data,
    )
    bonobo.run(graph, services=get_services(query))

    # Combine results of both chains in the graph.
    df = transform_data()
    return df


if __name__ == "__main__":

    # 1. Create an ArgumentParser object
    parser = argparse.ArgumentParser(
        description="A simple program that queries the YouTube data API"
    )

    # 2. Add arguments
    parser.add_argument("q", type=str, help="The query term")

    # 3. Parse the arguments
    args = parser.parse_args()

    # 4. Invoke main method
    main(args.q)
