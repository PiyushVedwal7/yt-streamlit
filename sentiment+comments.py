import streamlit as st
import requests
import re
import pandas as pd
import io
from textblob import TextBlob  



def fetch_comments(api_key, video_id):
    URL = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": api_key,
        "maxResults": 100
    }

    comments = []
    next_page_token = None

    while True:
        if next_page_token:
            params["pageToken"] = next_page_token

        response = requests.get(URL, params=params)

        if response.status_code == 200:
            data = response.json()

            for item in data.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
        else:
            st.error(f"Error: {response.json()}")
            break

    return comments



def extract_video_id(url):
    video_id = None

    match = re.search(r"(?<=v=)[\w-]+", url)

    if match:
        video_id = match.group(0)
    else:
        st.error("Invalid YouTube URL. Please provide a valid YouTube video URL.")
    return video_id



def save_comments_to_csv(comments):
    
    df = pd.DataFrame(comments, columns=["Comment"])


    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return csv_buffer.getvalue()



def analyze_sentiment(comments):
    sentiments = []
    for comment in comments:
        blob = TextBlob(comment)
        sentiment_score = blob.sentiment.polarity
        sentiment = 'Positive' if sentiment_score > 0 else 'Negative' if sentiment_score < 0 else 'Neutral'
        sentiments.append((comment, sentiment))
    return sentiments



def main():
    st.title("YouTube Comment Fetcher and Sentiment Analysis")

    page = st.sidebar.selectbox("Select a page:", ["Fetch Comments", "Sentiment Analysis"])

    if page == "Fetch Comments":
        st.header("YouTube Comment Fetcher")

        api_key = st.text_input("Enter your YouTube API Key:", "")
        video_url = st.text_input("Enter the YouTube Video URL:", "https://www.youtube.com/watch?v=nBzrMw8hkmY")

        video_id = extract_video_id(video_url)

        if 'comments' not in st.session_state:
            st.session_state.comments = []

        if st.button("Fetch Comments"):
            if api_key and video_id:
                # Fetch new comments on each click
                new_comments = fetch_comments(api_key, video_id)

                if new_comments:
                    st.session_state.comments = new_comments
                    st.success(f"Fetched {len(new_comments)} comments successfully.")
                else:
                    st.write("No comments found.")
            else:
                st.error("Please provide both the API Key and a valid YouTube Video URL.")

        if st.session_state.comments:
            st.subheader("Comments:")
            for comment in st.session_state.comments:
                st.write(f"- {comment}")

            # Save comments to CSV
            csv_data = save_comments_to_csv(st.session_state.comments)
            st.download_button(
                label="Download Comments as CSV",
                data=csv_data,
                file_name="youtube_comments.csv",
                mime="text/csv"
            )

    elif page == "Sentiment Analysis":
        st.header("Sentiment Analysis on YouTube Comments")

        if 'comments' not in st.session_state or not st.session_state.comments:
            st.error("Please fetch comments first on the 'Fetch Comments' page.")
        else:
            
            sentiments = analyze_sentiment(st.session_state.comments)

            st.subheader("Sentiment Analysis Results:")
            sentiment_data = pd.DataFrame(sentiments, columns=["Comment", "Sentiment"])
            st.write(sentiment_data)

            
            csv_data = save_comments_to_csv(sentiment_data['Comment'].tolist())  
            st.download_button(
                label="Download Sentiment Results as CSV",
                data=csv_data,
                file_name="youtube_comments_sentiment.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    main()
