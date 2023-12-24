# Import libraries
from datetime import datetime
import pandas as pd
import requests
import time
import logging

class RedditScraper:
    # Initialize RedditScraper with subreddit name, start date, and end date.
    def __init__(self, subreddit: str, start_date: str, end_date: str):
        self.logger = logging.getLogger("DigiKalaScraper")
        self.subreddit = subreddit
        self.url = f"https://www.reddit.com/r/{subreddit}/new.json?sort=new&limit=100"
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.columns = ["identifier", "ups", "User Engagement Ratio", "upvote ratio", "nummber of comments", "title length"]
        self.df = pd.DataFrame(columns=self.columns)
        self.TOTAL_SUCCESS = 0
        

        # Set up console logging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    #Fetch Reddit data using HTTP GET request and return status code and JSON response.
        

    def fetch_data(self, url, headers):
        retries = 5
        while retries > 0:

            # try, except
            try:
                # Create and return the resonse and status of the request. Note: the success or failure of the status will be checked in the Scrape function
                response = requests.get(url, headers, timeout=8)
                if response.status_code == 200:
                    self.TOTAL_SUCCESS += 1
                    self.logger.info(
                        f"[{self.TOTAL_SUCCESS}] Successful! [200]"
                    )
                    return response.json()
                else:
                    self.logger.warning(
                        f"Request failed with status code {response.status_code}. Retrying..."
                    )
                    retries -= 1
            except requests.Timeout as e:
                self.logger.warning("Request timed out. Retrying...")
                retries -= 1
            except requests.ConnectionError as e:
                self.logger.error(e)
                # Assuming ClientConnectorError was meant to handle connection errors
                # aiohttp's ClientConnectorError is equivalent to requests' ConnectionError
                retries -= 1
            time.sleep(0.1)
        self.logger.error("Max retries exceeded. Give up.")

    # Scrape Reddit posts within the specified date range and store in a DataFrame.
    def scrape(self):
        # This attribute contains the identifier of the first elemnt in the next JSON, This way we somehow create a chain of JSON identifiers
        after = None

        # Scrape Reddit for a desired subreddit
        while True:
            data = self.fetch_data(self.url if after is None else f"{self.url}&after={after}", {"User-agent": 'your bot 0.1'})
            # Check if the request was successful
            after, flag = self.extract_posts(data)
            # If after is empty or the desired range passed, show the error and break the loop
            if not after or flag:
                print("End of scraping")
                break

        return self.df

    # Extract posts from Reddit data and add them to dataframe based on date range.
    def extract_posts(self, data):
        after = None
        flag = False

        # Extract the data and save our metrics in a dataframe
        if "data" in data and "children" in data["data"]:
            for child in data["data"]["children"]:
                post_data = child.get("data", {})

                # Convert the time of the post to the utc format. We only need year, month, day
                post_timestamp = datetime.utcfromtimestamp(post_data.get("created_utc", 0)).strftime("%Y-%m-%d")
                """ Check the time of the post with the desired range.
                    Choose our metrics. I chose ups, downs, upvote_ratio, num_comments, post_timestamp as the metrics
                    Note: the attribute 'name' here is the identifier of the post
                   """
                
                # Calculate user ingagement ratio
                subsribers = post_data.get('subreddit_subscribers')
                u_ingagement_ratio = post_data.get("ups")/subsribers
                # Check if the post timestamp is in the range
                if self.start_date <= datetime.strptime(post_timestamp, "%Y-%m-%d") <= self.end_date:
                    new_data = [post_data.get("name"), post_data.get("ups"), u_ingagement_ratio,
                                post_data.get("upvote_ratio"), post_data.get("num_comments"), len(post_data.get("title"))]
                
                    # Add the scraped post's information to dataframe
                    self.df.loc[len(self.df)] = new_data
                
                # Check the time stamp and change the flag to True if it is outside the range. 
                elif self.is_outside_date_range(post_timestamp):
                    return post_data.get("name"), True
                
            # Set the last post's identifier for the next requst
            after = post_data.get("name")

        return after, flag
    
    # Check if the post timestamp is outside the specified date range.
    def is_outside_date_range(self, post_timestamp):
        return datetime.strptime(post_timestamp, "%Y-%m-%d") < self.start_date
    
    # Save the dataframe to the CSV file
    def save_to_csv(self, filename: str):
        """
        Save DataFrame to a CSV file.
        """
        try:
            self.df.to_csv(filename, index=False)
            print(f"DataFrame saved to {filename}")
        except Exception as e:
            print(f"Error occurred while saving DataFrame: {e}")

# main
if __name__ == "__main__":
    # Replace these three attributes with your desire subreddit, start and end time
    subreddit = "vim"
    start_date = "2023-09-23"
    end_date = "2023-12-20"
    
    # Call the scraper
    scraper = RedditScraper(subreddit, start_date, end_date)
    result_df = scraper.scrape()

     # Save DataFrame to a CSV file
    scraper.save_to_csv(f"Datasets\{subreddit}.csv")
