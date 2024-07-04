from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object('config.Config')
db = SQLAlchemy(app)

from models import User, Subreddit, Post, Comment, Upvote, Subscription

# Routes and views
@app.route('/')
def home():
    subreddits = Subreddit.query.all()
    return render_template('home.html', subreddits=subreddits)

@app.route('/subreddits/<int:subreddit_id>/posts', methods=['GET'])
def get_subreddit_posts(subreddit_id):
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    posts = Post.query.filter_by(subreddit_id=subreddit_id).order_by(Post.creation_time.desc()).limit(limit).offset(offset).all()
    return jsonify([post.to_dict() for post in posts])

@app.route('/subreddits/<int:subreddit_id>/subscribe', methods=['POST'])
def subscribe_subreddit(subreddit_id):
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    subscription = Subscription(user_id=user_id, subreddit_id=subreddit_id)
    db.session.add(subscription)
    db.session.commit()
    return jsonify({"message": "Subscribed successfully"}), 201

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

@app.route('/posts/<int:post_id>/upvote', methods=['POST'])
def upvote_post(post_id):
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    upvote = Upvote(user_id=user_id, post_id=post_id)
    db.session.add(upvote)
    db.session.commit()
    return jsonify({"message": "Upvoted successfully"}), 201

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

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    subscriptions = Subscription.query.filter_by(user_id=user_id).all()
    upvotes = Upvote.query.filter_by(user_id=user_id).all()
    return jsonify({
        "user": {
            "username": user.username,
            "email": user.email
        },
        "subscriptions": [sub.to_dict() for sub in subscriptions],
        "upvotes": [upvote.to_dict() for upvote in upvotes]
    })

if __name__ == '__main__':
    app.run(debug=True)
