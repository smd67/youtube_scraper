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
import re

import googleapiclient.discovery
import pandas as pd
from download import download
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fuzzywuzzy import fuzz
from nltk.sentiment import SentimentIntensityAnalyzer
from pydantic import BaseModel
from tabulate import tabulate

# 01234567890123456789012345678901234567890123456789012345678901234567890123456789012345

class Query(BaseModel):
    """
    Pydantic representation of a query.
    """

    query_string: str


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
def do_query(query: Query) -> JSONResponse:
    """
    API endpoint to start the query.

    Parameters
    ----------
    query : Query
        Pydantic class that represents a query.

    Returns
    -------
    JSONResponse
        A JSON object
    """
    df = main(query.query_string)
    json_string = df.to_dict(orient="records")  # 'records' is a common format
    print("=================")
    print(json_string)
    print("=================")
    return JSONResponse(content=json_string)


def extract_search_data(
    instance: googleapiclient.discovery.Resource, query: str
) -> dict:
    """
    Search for videos that match a query string.

    Parameters
    ----------
    instance : googleapiclient.discovery.Resource
        The YouTube instance to query.
    query : str
        The query string used in the "q" parameter.

    Returns
    -------
    str
        The json data from the response.
    """
    response = {}
    try:
        request = instance.search().list(
            part="snippet", q=query, maxResults=250
        )
        response = request.execute()
    except googleapiclient.errors.HttpError as e:
        print(f"Error: unexpected exception e={e}")
    return response


def extract_comment_thread_data(
    instance: googleapiclient.discovery.Resource, search_data: dict
) -> dict:
    """
    Extract comments for all of the videos.

    Parameters
    ----------
    instance : googleapiclient.discovery.Resource
        YouTube instance to query
    search_data : dict
        Dictionary containing the search data.

    Returns
    -------
    list
        A list of comment threads.
    """
    data = {}
    data["items"] = []
    for item in search_data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if video_id:
            try:
                request = instance.commentThreads().list(
                    part="id, replies, snippet", videoId=video_id
                )
                response = request.execute()

                data["items"].append(response)
            except googleapiclient.errors.HttpError:
                pass
    return data


def extract_channel_data(
    instance: googleapiclient.discovery.Resource, search_data: dict
) -> dict:
    """
    Extract comments for all of the videos.

    Parameters
    ----------
    instance : googleapiclient.discovery.Resource
        YouTube instance to query
    search_data : dict
        Dictionary containing the search data.

    Returns
    -------
    list
        A list of comment threads.
    """
    data = {}
    data["items"] = []
    channel_ids = set()
    for item in search_data.get("items", []):
        channel_id = item.get("snippet", {}).get("channelId")
        if channel_id not in channel_ids:
            request = instance.channels().list(
                part="id, statistics, snippet", id=channel_id
            )
            response = request.execute()
            data["items"].append(response)
            channel_ids.add(channel_id)
    return data


def transform_search_data(search_data: dict) -> pd.DataFrame:
    """
    Extract the channel id and channel title from the json data.

    Parameters
    ----------
    search_data : dict
        The json data returned from the search query above.
    """
    data = []
    for item in search_data.get("items", []):
        snippet = item.get("snippet", {})
        channel_tuple = (
            snippet.get("channelId", ""),
            snippet.get("channelTitle", ""),
            snippet.get("description", ""),
        )
        data.append(channel_tuple)
    df = pd.DataFrame(data, columns=["Id", "Title", "Description"])
    return df


def perform_sentiment_analysis(text: str) -> float:
    # Initialize VADER sentiment analyzer
    sid = SentimentIntensityAnalyzer()
    # Perform sentiment analysis
    sentiment_score = sid.polarity_scores(text)["pos"]
    return sentiment_score


def transform_comment_thread_data(comment_thread_data: dict) -> pd.DataFrame:
    """
    Transform the comment_thread_data into a useable dataframe.
    Parameters
    ----------
    comment_thread_data : dict
        A dictionary containing the comment thread data.

    Returns
    -------
    pd.DataFrame
        A useble dataframe
    """
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
    df = pd.DataFrame(data, columns=["Channel Id", "Score"])
    grouped_data = df.groupby("Channel Id")["Score"].mean()
    result_df = grouped_data.reset_index()
    return result_df


def transform_channel_data(query: str, channel_data: dict) -> pd.DataFrame:
    """
    Transform the channel_data into a useable dataframe.
    Parameters
    ----------
    comment_thread_data : dict
        A dictionary containing the channel data.

    Returns
    -------
    pd.DataFrame
        A useble dataframe
    """
    data = []
    for item in channel_data.get("items", []):
        for channel_item in item.get("items", []):
            channel_id = channel_item.get("id", "")
            custom_url = channel_item.get("snippet", {}).get("customUrl", "")
            url = f"https://www.youtube.com/{custom_url}"
            title = channel_item.get("snippet", {}).get("title", "")
            description = channel_item.get("snippet", {}).get("description", "")
            sim_score = fuzzy_similarity(query, description)
            video_count = channel_item.get("statistics", {}).get(
                "videoCount", ""
            )
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
            "Channel Id",
            "Title",
            "Url",
            "Description",
            "Videos",
            "Subscribers",
            "Similarity",
        ],
    )
    return df


def transform_data(
    query: str, comment_thread_data: dict, channel_data: dict
) -> pd.DataFrame:
    """
    Tranforms the extracted data into a single dataframe.

    Parameters
    ----------
    comment_thread_data : dict
        JSON dictionary containing comment thread results.

    channel_data : dict
        JSON dictionary containing channel results.

    Returns
    -------
    pd.DataFrame
        A combined dataframe with elements from the channel and comment threads.
    """
    comment_thread_df = transform_comment_thread_data(comment_thread_data)
    channel_df = transform_channel_data(query, channel_data)
    combined_df = pd.merge(channel_df, comment_thread_df, on="Channel Id")
    combined_df["Videos Rank"] = combined_df["Videos"].rank(
        method="dense", ascending=False
    )
    combined_df["Subscribers Rank"] = combined_df["Subscribers"].rank(
        method="dense", ascending=False
    )
    combined_df["Score Rank"] = combined_df["Score"].rank(
        method="dense", ascending=False
    )
    combined_df["Similarity Rank"] = combined_df["Similarity"].rank(
        method="dense", ascending=False
    )
    combined_df["Average Rank"] = (
        combined_df["Videos Rank"]
        + combined_df["Subscribers Rank"]
        + combined_df["Score Rank"]
        + combined_df["Similarity Rank"]
    ) / 4.0

    combined_df = combined_df.sort_values(by="Average Rank")
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
    float
        A ratio between 0 and 1 representing how similar the match is.
    """
    str1 = str1.lower()
    str2 = str2.lower()

    pattern_words = re.findall(r"\w+", str1)

    best_ratio = 0
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

    api_service_name = "youtube"
    api_version = "v3"
    api_key = os.environ.get("DEVELOPER_KEY")

    download()

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=api_key
    )

    search_data = extract_search_data(youtube, query)
    comment_thread_data = extract_comment_thread_data(youtube, search_data)
    channel_data = extract_channel_data(youtube, search_data)

    df = transform_data(query, comment_thread_data, channel_data)
    print(tabulate(df, headers=df.columns, tablefmt="grid"))
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
