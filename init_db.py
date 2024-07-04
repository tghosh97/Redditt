from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from werkzeug.security import generate_password_hash

# Your models import
from app import Base, User, Subreddit, Post, Comment, Upvote, Subscription

# Create engine and session
engine = create_engine('sqlite:///reddit.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

# Create tables (only needed if you haven't already created them)
Base.metadata.create_all(engine)

# Create initial data
users = [
    User(username='user1', email='user1@example.com', password_hash=generate_password_hash('password1')),
    User(username='user2', email='user2@example.com', password_hash=generate_password_hash('password2')),
]

subreddits = [
    Subreddit(name='subreddit1', description='Description of subreddit1'),
    Subreddit(name='subreddit2', description='Description of subreddit2'),
]

posts = [
    Post(title='First Post', content='Content of the first post', user_id=1, subreddit_id=1),
    Post(title='Second Post', content='Content of the second post', user_id=2, subreddit_id=2),
]

comments = [
    Comment(content='First comment', post_id=1, user_id=2),
    Comment(content='Second comment', post_id=2, user_id=1),
]

upvotes = [
    Upvote(post_id=1, user_id=2),
    Upvote(post_id=2, user_id=1),
]

subscriptions = [
    Subscription(user_id=1, subreddit_id=1),
    Subscription(user_id=2, subreddit_id=2),
]

# Add to session and commit
session.add_all(users)
session.add_all(subreddits)
session.add_all(posts)
session.add_all(comments)
session.add_all(upvotes)
session.add_all(subscriptions)

session.commit()

# Close session
session.close()