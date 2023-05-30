import os
import praw
import json

class Reddit:
    description = "Returns a list of top posts from a subreddit."
    module_hook = "Chat_request_inner"

    def __init__(self, ml):
        self.ml = ml
        self.ch = ml.ch

        # PRAW configuration
        credentials = self.load_credentials("reddit_credentials.json")
        self.reddit = praw.Reddit(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            user_agent=credentials["user_agent"],
        )

    def main(self, arg, stop_event):
        subreddit = self.parse_subreddit(arg)
        posts = self.get_top_posts(subreddit)
        return self.format_posts(posts)

    def parse_subreddit(self, arg):
        if not arg or arg.lower() == "none":
            return "popular"
        elif "r/" in arg:
            return arg.replace("r/", "")
        else:
            return arg

    def get_top_posts(self, subreddit):
        try:
            subreddit = self.reddit.subreddit(subreddit)
            top_posts = subreddit.top(limit=5)  # Change the limit as needed

            posts = []
            for post in top_posts:
                post_title = post.title
                post_url = post.url
                posts.append({"title": post_title, "url": post_url})

            return posts

        except Exception as e:
            print("Error:", e)
            return "Error: Unable to fetch the top posts from the subreddit."

    def format_posts(self, posts):
        if isinstance(posts, str):
            return posts

        if not posts:
            return "No top posts found."

        output = "Top Posts:\n\n"
        for index, post in enumerate(posts, start=1):
            output += f"{index}. {post['title']}\n"
            output += f"   Link: {post['url']}\n\n"

        return output

    def load_credentials(self, filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(current_dir, filename)
        with open(filepath) as file:
            credentials = json.load(file)
        return credentials
