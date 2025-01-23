from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for,flash  # Add render/ # Add session here
from app.models import User, Post, Comment, Follow, db
from flask_sqlalchemy import SQLAlchemy
from app import bcrypt
from flask import redirect


main = Blueprint('main', __name__)

@main.route('/')
def home():
    """Landing page or feed based on login status."""
    if 'user_id' in session:  # Check if user is logged in
        user_id = session['user_id']

        # Fetch posts from users the logged-in user follows
        following_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=user_id).all()]
        print(f"Following IDs for user {user_id}: {following_ids}")
        
        if following_ids:  # If the user is following others
            posts = Post.query.filter(Post.user_id.in_(following_ids)).order_by(Post.timestamp.desc()).all()
            print(f"Posts fetched: {posts}")
        else:  # If the user isn't following anyone, show global posts
            posts = Post.query.order_by(Post.timestamp.desc()).all()

        # Render the feed for logged-in users
        return render_template('feed.html', posts=posts)
    else:
        # Render the landing page for guests
        return render_template('landing.html')



# --- Authentication Routes ---

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user."""
    if request.method == 'GET':
        # Render the login page for GET requests
        return render_template('login.html')

    # Handle POST requests
    data = request.form  # Handle form-encoded data
    email = data.get('email')
    password = data.get('password')

    # Ensure email and password are provided
    if not email or not password:
        flash('Email and password are required', 'danger')
        return redirect(url_for('main.login'))

    # Authenticate user
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        # Save user ID in session
        session['user_id'] = user.id
        flash('Login successful', 'success')
        return redirect(url_for('main.home'))  # Redirect to the home page after login
    else:
        flash('Invalid email or password', 'danger')
        return redirect(url_for('main.login'))



@main.route('/logout', methods=['POST'])
def logout():
    """Log out the current user."""
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'})


@main.route('/signup', methods=['GET', 'POST'])
def signup():
    """Sign up a new user."""
    if request.method == 'GET':
        # Determine user type from query parameters (e.g., ?type=professional or ?type=standard)
        user_type = request.args.get('type', 'standard')  # Default to standard user

        if user_type == 'professional':
            # Render the professional signup form
            return render_template('signup_professional.html')
        else:
            # Render the standard signup form
            return render_template('signup_standard.html')

    # Handle POST request for signup
    username = request.form['username']
    email = request.form['email']
    password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
    is_professional = request.form.get('is_professional', 'false') == 'true'

    # Additional fields for professionals
    license_number = request.form.get('license')  # Optional, only for professionals
    specialization = request.form.get('specialization')  # Optional, only for professionals

    # Check if the email is already registered
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400

    # Create the user
    new_user = User(username=username, email=email, password=password, is_professional=is_professional)
    db.session.add(new_user)
    db.session.commit()

    # Save professional details if applicable
    if is_professional:
        # Save the license number and specialization to another table if needed
        pass

    return jsonify({'message': 'User created successfully', 'user_id': new_user.id}), 201



# --- Feed and Post Routes ---

@main.route('/feed/<int:user_id>', methods=['GET'])
def feed(user_id):
    """Fetch posts from users the current user follows."""
    # Fetch IDs of users the logged-in user follows
    following = [follow.followed_id for follow in Follow.query.filter_by(follower_id=user_id).all()]

    # Include the user's own posts in the feed
    following.append(user_id)

    # Fetch posts, ordered by timestamp
    posts = Post.query.filter(Post.user_id.in_(following)).order_by(Post.timestamp.desc()).all()

    # Return posts as JSON
    return jsonify([
        {
            'id': post.id,
            'author': post.author.username,
            'author_pic': post.author.profile_pic,
            'content': post.content,
            'image': post.image,
            'timestamp': post.timestamp.isoformat(),
            'likes': len(post.likes),
            'comments': len(post.comments)
        }
        for post in posts
    ])


@main.route('/post', methods=['POST'])
def create_post():
    """Create a new post."""
    data = request.json
    post = Post(content=data['content'], image=data.get('image'), user_id=data['user_id'])
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Post created successfully', 'post_id': post.id}), 201


@main.route('/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Fetch a specific post."""
    post = Post.query.get_or_404(post_id)
    return jsonify({
        'id': post.id,
        'author': post.author.username,
        'author_pic': post.author.profile_pic,
        'content': post.content,
        'image': post.image,
        'timestamp': post.timestamp.isoformat(),
        'likes': len(post.likes),
        'comments': [{'id': comment.id, 'content': comment.content, 'author': comment.user_id} for comment in post.comments]
    })


# --- Like Routes ---

@main.route('/post/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """Like or unlike a post."""
    user_id = request.json['user_id']
    existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()

    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({'message': 'Like removed'})
    else:
        new_like = Like(user_id=user_id, post_id=post_id)
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'message': 'Post liked'})


# --- Comment Routes ---

@main.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    """Add a comment to a post."""
    data = request.json
    comment = Comment(content=data['content'], user_id=data['user_id'], post_id=post_id)
    db.session.add(comment)
    db.session.commit()
    return jsonify({'message': 'Comment added successfully', 'comment_id': comment.id}), 201


@main.route('/post/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """Fetch all comments for a post."""
    comments = Comment.query.filter_by(post_id=post_id).all()
    return jsonify([
        {'id': comment.id, 'content': comment.content, 'author': comment.user_id, 'timestamp': comment.timestamp.isoformat()}
        for comment in comments
    ])


# --- Follow Routes ---

@main.route('/follow/<int:user_id>', methods=['POST'])
def follow(user_id):
    """Follow or unfollow a user."""
    current_user_id = request.json['current_user_id']
    existing_follow = Follow.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()

    if existing_follow:
        db.session.delete(existing_follow)
        db.session.commit()
        return jsonify({'message': 'Unfollowed successfully'})
    else:
        new_follow = Follow(follower_id=current_user_id, followed_id=user_id)
        db.session.add(new_follow)
        db.session.commit()
        return jsonify({'message': 'Followed successfully'})


@main.route('/followers/<int:user_id>', methods=['GET'])
def get_followers(user_id):
    """Fetch all followers of a user."""
    followers = Follow.query.filter_by(followed_id=user_id).all()
    return jsonify([
        {'id': follow.follower_id, 'username': follow.follower.username}
        for follow in followers
    ])


@main.route('/following/<int:user_id>', methods=['GET'])
def get_following(user_id):
    """Fetch all users the current user is following."""
    following = Follow.query.filter_by(follower_id=user_id).all()
    return jsonify([
        {'id': follow.followed_id, 'username': follow.followed.username}
        for follow in following
    ])
