import streamlit as st
import requests
import re
import pandas as pd
import io


def get_live_broadcast_id(api_key, video_id):
    URL = f"https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={video_id}&key={api_key}"
    response = requests.get(URL)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        if items:
            live_stream_details = items[0].get("liveStreamingDetails", {})
            live_chat_id = live_stream_details.get("activeLiveChatId")
            return live_chat_id
        else:
            st.error("The video is not a live stream.")
            return None
    else:
        st.error(f"Error fetching video details: {response.json()}")
        return None

# Function to fetch live chat messages using live chat ID
def fetch_live_chat_messages(api_key, live_chat_id):
    URL = "https://www.googleapis.com/youtube/v3/liveChat/messages"
    params = {
        "part": "snippet",
        "liveChatId": live_chat_id,
        "key": api_key,
        "maxResults": 100  # Max comments per request
    }

    comments = []
    next_page_token = None

    # Loop through pages of live chat messages if they exist
    while True:
        if next_page_token:
            params["pageToken"] = next_page_token

        response = requests.get(URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                comment = item["snippet"]["displayMessage"]
                comments.append(comment)

            # Check if there's another page of chat messages
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break  # No more pages of chat messages
        else:
            st.error(f"Error: {response.json()}")
            break
    
    return comments

# Function to extract Video ID from YouTube URL
def extract_video_id(url):
    video_id = None
    # Regular expression to match YouTube video URL patterns
    match = re.search(r"(?<=v=)[\w-]+", url)
    
    if match:
        video_id = match.group(0)
    else:
        st.error("Invalid YouTube URL. Please provide a valid YouTube video URL.")
    return video_id

# Function to save comments as a CSV
def save_comments_to_csv(comments):
    # Convert the list of comments to a pandas DataFrame
    df = pd.DataFrame(comments, columns=["Comment"])
    
    # Convert the DataFrame to CSV in-memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer.getvalue()

# Streamlit UI
def main():
    st.title("YouTube Live Stream Comment Fetcher")
    
    # Input for API Key and YouTube Video URL
    api_key = st.text_input("Enter your YouTube API Key:", "")
    video_url = st.text_input("Enter the YouTube Video URL for the live stream:", "https://www.youtube.com/watch?v=nBzrMw8hkmY")
    
    # Extract Video ID from URL
    video_id = extract_video_id(video_url)

    # Initialize session state for storing comments
    if 'comments' not in st.session_state:
        st.session_state.comments = []

    # Button to fetch comments
    if st.button("Fetch Live Stream Comments"):
        if api_key and video_id:
            # Step 1: Get live chat ID from video ID
            live_chat_id = get_live_broadcast_id(api_key, video_id)
            
            if live_chat_id:
                # Step 2: Fetch live chat messages
                new_comments = fetch_live_chat_messages(api_key, live_chat_id)
                
                # If new comments are fetched, update the session state
                if new_comments:
                    st.session_state.comments = new_comments
                else:
                    st.write("No comments found.")
            else:
                st.write("Could not retrieve live chat ID.")
        else:
            st.error("Please provide both the API Key and a valid YouTube Video URL.")
    
    # Display comments
    if st.session_state.comments:
        st.subheader("Live Stream Comments:")
        for comment in st.session_state.comments:
            st.write(f"- {comment}")

        # Add a download button for the comments CSV
        csv_data = save_comments_to_csv(st.session_state.comments)
        st.download_button(
            label="Download Comments as CSV",
            data=csv_data,
            file_name="youtube_live_stream_comments.csv",
            mime="text/csv"
        )
    
# Run the Streamlit app
if __name__ == "__main__":
    main()
