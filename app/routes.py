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
        posts = Post.query.filter(Post.user_id.in_(following_ids)).order_by(Post.timestamp.desc()).all()

        # Render the feed for logged-in users
        return render_template('feed.html', posts=posts)
    else:
        # Render the landing page for guests
        return render_template('landing.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Authenticate user
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id  # Save user ID in session
            return redirect(url_for('main.home'))  # Redirect to home/feed
        else:
            return "Invalid email or password", 401

    # Render login form
    return render_template('login.html')


    # Find user by email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User does not exist'}), 404

    # Check the password
    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid password'}), 401

    # Simulate session-based login (for web or token generation for mobile)
    session['user_id'] = user.id
    return jsonify({'message': f'Welcome {user.username}', 'user_id': user.id})

@main.route('/logout', methods=['POST'])
def logout():
    """Log out the current user."""
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'})


@main.route('/signup-standard', methods=['GET', 'POST'])
def signup_standard():
    """Sign up as a Standard User."""
    if request.method == 'POST':
        # Use 'username' as it matches the name attribute in the HTML form
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        # Check if the email already exists
        if User.query.filter_by(email=email).first():
            return "Email already registered", 400

        # Create a new user
        new_user = User(username=username, email=email, password=password, is_professional=False)
        db.session.add(new_user)
        db.session.commit()

        # Log in the user
        session['user_id'] = new_user.id
        return redirect(url_for('main.home'))

    # Render the sign-up form
    return render_template('signup_standard.html')



@main.route('/signup_professional', methods=['GET', 'POST'])
def signup_professional():
    """Sign up as a Professional User."""
    if request.method == 'POST':
        name = request.form['name']  # Fetch the full name
        email = request.form['email']  # Fetch the email
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')  # Hash the password

        # Check if the email is already registered
        if User.query.filter_by(email=email).first():
            return "Email already registered", 400

        # Create a new user marked as a professional
        new_user = User(username=name, email=email, password=password, is_professional=True)
        db.session.add(new_user)
        db.session.commit()

        # Log in the user
        session['user_id'] = new_user.id
        return redirect(url_for('main.home'))

    # Render the professional signup form
    return render_template('signup_professional.html')




# --- User Routes ---

@main.route('/profile/<int:user_id>', methods=['GET'])
def profile(user_id):
    """Fetch user profile and posts."""
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).all()
    return jsonify({
        'username': user.username,
        'bio': user.bio,
        'profile_pic': user.profile_pic,
        'posts': [{'content': post.content, 'timestamp': post.timestamp} for post in posts]
    })

@main.route('/update-profile', methods=['POST'])
def update_profile():
    """Update user profile details."""
    data = request.json
    user = User.query.get_or_404(data['user_id'])
    user.bio = data.get('bio', user.bio)
    user.profile_pic = data.get('profile_pic', user.profile_pic)
    db.session.commit()
    return {'message': 'Profile updated successfully'}

# --- Follow Routes ---

@main.route('/follow/<int:user_id>', methods=['POST'])
def follow(user_id):
    """Follow or unfollow a user."""
    current_user_id = request.json['current_user_id']
    existing_follow = Follow.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()

    if existing_follow:
        db.session.delete(existing_follow)
        db.session.commit()
        return {'message': 'Unfollowed successfully'}
    else:
        new_follow = Follow(follower_id=current_user_id, followed_id=user_id)
        db.session.add(new_follow)
        db.session.commit()
        return {'message': 'Followed successfully'}

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

# --- Post Routes ---

@main.route('/post', methods=['POST'])
def create_post():
    """Create a new post."""
    data = request.json
    post = Post(content=data['content'], image=data.get('image'), user_id=data['user_id'])
    db.session.add(post)
    db.session.commit()
    return {'message': 'Post created successfully'}

@main.route('/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Fetch a specific post."""
    post = Post.query.get_or_404(post_id)
    return jsonify({
        'content': post.content,
        'image': post.image,
        'timestamp': post.timestamp,
        'author': post.author.username,
        'comments': [{'content': comment.content, 'author': comment.user_id} for comment in post.comments],
        'likes': len(post.likes)
    })

@main.route('/feed/<int:user_id>', methods=['GET'])
def feed(user_id):
    """Fetch posts from users the current user follows."""
    following = [follow.followed_id for follow in Follow.query.filter_by(follower_id=user_id).all()]
    posts = Post.query.filter(Post.user_id.in_(following)).order_by(Post.timestamp.desc()).all()
    return jsonify([
        {
            'author': post.author.username,
            'content': post.content,
            'image': post.image,
            'timestamp': post.timestamp,
            'comments': len(post.comments),
            'likes': len(post.likes)
        }
        for post in posts
    ])

# --- Comment Routes ---

@main.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    """Add a comment to a post."""
    data = request.json
    comment = Comment(content=data['content'], user_id=data['user_id'], post_id=post_id)
    db.session.add(comment)
    db.session.commit()
    return {'message': 'Comment added successfully'}

@main.route('/post/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """Fetch all comments for a post."""
    comments = Comment.query.filter_by(post_id=post_id).all()
    return jsonify([
        {'content': comment.content, 'author': comment.user_id, 'timestamp': comment.timestamp}
        for comment in comments
    ])

# --- Like Routes ---

@main.route('/post/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """Like or unlike a post."""
    user_id = request.json['user_id']
    existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()

    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        return {'message': 'Like removed'}
    else:
        new_like = Like(user_id=user_id, post_id=post_id)
        db.session.add(new_like)
        db.session.commit()
        return {'message': 'Post liked'}
