from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

# Create engine
engine = create_engine('sqlite:///reddit.db', echo=True)  # echo=True for debug output

# Create a sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

# Declare Base
Base = declarative_base()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reddit.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Optional: Disable modification tracking

# Bind SQLAlchemy instance to the Flask app
db = SQLAlchemy(app)

# Define models
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    posts = relationship('Post', backref='author', lazy=True)
    comments = relationship('Comment', backref='author', lazy=True)
    subscriptions = relationship('Subscription', backref='user', lazy=True)
    upvotes = relationship('Upvote', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }

class Subreddit(Base):
    __tablename__ = 'subreddit'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class Post(Base):
    __tablename__ = 'post'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(String, nullable=False)
    creation_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    subreddit_id = Column(Integer, ForeignKey('subreddit.id'), nullable=False)
    comments = relationship('Comment', backref='post', lazy=True)
    upvotes = relationship('Upvote', backref='post', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'creation_time': self.creation_time.isoformat(),
            'user_id': self.user_id,
            'subreddit_id': self.subreddit_id
        }

class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    creation_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'creation_time': self.creation_time.isoformat(),
            'post_id': self.post_id,
            'user_id': self.user_id
        }

class Upvote(Base):
    __tablename__ = 'upvote'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id
        }

class Subscription(Base):
    __tablename__ = 'subscription'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    subreddit_id = Column(Integer, ForeignKey('subreddit.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subreddit_id': self.subreddit_id
        }

# Create all tables
Base.metadata.create_all(engine)

# Close session
session.close()

# Define routes and views
# Route to get subreddit posts by subreddit_id
@app.route('/subreddits/<int:subreddit_id>/posts', methods=['GET'])
def get_subreddit_posts(subreddit_id):
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    posts = Post.query.filter_by(subreddit_id=subreddit_id).order_by(Post.creation_time.desc()).limit(limit).offset(offset).all()
    return jsonify([post.to_dict() for post in posts])

# Route to subscribe to a subreddit
@app.route('/subreddits/<int:subreddit_id>/subscribe', methods=['POST'])
def subscribe_subreddit(subreddit_id):
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    subscription = Subscription(user_id=user_id, subreddit_id=subreddit_id)
    db.session.add(subscription)
    db.session.commit()
    return jsonify({"message": "Subscribed successfully"}), 201

# Route to create a new post in a subreddit
@app.route('/subreddits/<int:subreddit_id>/posts', methods=['POST'])
def create_post(subreddit_id):
    user_id = request.json.get('user_id')
    title = request.json.get('title')
    content = request.json.get('content')
    if not all([user_id, title, content]):
        return jsonify({"error": "user_id, title, and content are required"}), 400
    post = Post(user_id=user_id, subreddit_id=subreddit_id, title=title, content=content)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201

# Route to upvote a post
@app.route('/posts/<int:post_id>/upvote', methods=['POST'])
def upvote_post(post_id):
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    upvote = Upvote(user_id=user_id, post_id=post_id)
    db.session.add(upvote)
    db.session.commit()
    return jsonify({"message": "Upvoted successfully"}), 201

# Route to comment on a post
@app.route('/posts/<int:post_id>/comments', methods=['POST'])
def comment_post(post_id):
    user_id = request.json.get('user_id')
    content = request.json.get('content')
    if not all([user_id, content]):
        return jsonify({"error": "user_id and content are required"}), 400
    comment = Comment(user_id=user_id, post_id=post_id, content=content)
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_dict()), 201

# Route to get user profile with subscriptions and upvotes
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    subscriptions = Subscription.query.filter_by(user_id=user_id).all()
    upvotes = Upvote.query.filter_by(user_id=user_id).all()
    return jsonify({
        "user": user.to_dict(),
        "subscriptions": [sub.to_dict() for sub in subscriptions],
        "upvotes": [upvote.to_dict() for upvote in upvotes]
    })

if __name__ == '__main__':
    app.run(debug=True)
