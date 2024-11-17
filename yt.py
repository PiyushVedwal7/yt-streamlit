import streamlit as st
import requests
import re
import pandas as pd
import io

# Function to fetch comments from a YouTube video with pagination
def fetch_comments(api_key, video_id):
    URL = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": api_key,
        "maxResults": 100  # Set to maximum allowed comments per request
    }

    comments = []
    next_page_token = None

    # Loop through pages of comments if they exist
    while True:
        if next_page_token:
            params["pageToken"] = next_page_token

        response = requests.get(URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            for item in data.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)

            # Check if there's another page of comments
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break  # No more pages of comments
        else:
            st.error(f"Error: {response.json()}")
            break
    
    return comments

# Function to extract Video ID from a YouTube URL
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
    st.title("YouTube Comment Fetcher")
    
    # Input for API Key and YouTube Video URL
    api_key = st.text_input("Enter your YouTube API Key:", "")
    video_url = st.text_input("Enter the YouTube Video URL:", "https://www.youtube.com/watch?v=nBzrMw8hkmY")
    
    # Extract Video ID from URL
    video_id = extract_video_id(video_url)

    # Initialize session state for storing comments
    if 'comments' not in st.session_state:
        st.session_state.comments = []

    # Button to fetch comments
    if st.button("Fetch Comments"):
        if api_key and video_id:
            # Fetch new comments on each click
            new_comments = fetch_comments(api_key, video_id)
            
            # If new comments are fetched, update the session state
            if new_comments:
                st.session_state.comments = new_comments
            else:
                st.write("No comments found.")
        else:
            st.error("Please provide both the API Key and a valid YouTube Video URL.")
    
    # Display comments
    if st.session_state.comments:
        st.subheader("Comments:")
        for comment in st.session_state.comments:
            st.write(f"- {comment}")

        # Add a download button for the comments CSV
        csv_data = save_comments_to_csv(st.session_state.comments)
        st.download_button(
            label="Download Comments as CSV",
            data=csv_data,
            file_name="youtube_comments.csv",
            mime="text/csv"
        )
    
# Run the Streamlit app
if __name__ == "__main__":
    main()
