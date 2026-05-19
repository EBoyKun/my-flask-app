import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy  # Import the extension
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Tells Flask where to send users if they aren't logged in

# Secret key required by Flask to keep user sessions secure from tampering
# app.config['SECRET_KEY'] = 'super-secret-key-change-this-in-production'
# updated code for better security
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')


# Tell Flask to use SQLite and name the database file 'guestbook.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///guestbook.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database object
db = SQLAlchemy(app)

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True) # Unique ID for each row
    name = db.Column(db.String(100), nullable=False) # The visitor's name

    def __repr__(self):
        return f'<Visitor {self.name}>'

@app.route("/")
def home():
  return render_template("home.html", name="Developer")

@app.route("/about")
def about():
  return render_template("about.html")

@app.route("/portfolio")
def portfolio():
  my_projects = ["Python Web Scraper", "Flask Blog", "Weather Bashboard App"]
  return render_template("portfolio.html", projects=my_projects)

# OLD MISTAKE TO REMEMBER WHAT NOT TO DO
# @app.route("/greet", methods=["GET", "POST"])
# def greet():
#   if request.method == "POST":
#     # This triggers when the user submits the form
#     username = request.form.get("user_name")
#     return f"Hello, {username}! Your data reached the backend."
      
#   # This triggers when they just visit the page normally
#   all_visitors = Visitor.query.all() 
#   return render_template("greet.html", visitors=all_visitors)

@app.route("/greet", methods=["GET", "POST"])
def greet():
    if request.method == "POST":
        username = request.form.get("user_name")
        
        if username:
            # 1. Package the typed name into our database blueprint
            new_visitor = Visitor(name=username)
            
            # 2. Save it to the guestbook.db file
            db.session.add(new_visitor)
            db.session.commit()
            
            # 3. CRITICAL: Clear the form and reload the page fresh
            return redirect(url_for('greet'))
        
    # 4. This runs on a normal page load (GET) OR right after the redirect above.
    # It grabs ALL names from the database and sends them to the HTML.
    all_visitors = Visitor.query.all() 
    return render_template("greet.html", visitors=all_visitors)

@app.route("/delete/<int:visitor_id>", methods=["POST"])
@login_required # 👈 THIS IS THE LOCK! Only logged-in users can run this function now.
def delete_visitor(visitor_id):
    # Find the specific visitor by their unique ID number
    visitor_to_delete = Visitor.query.get_or_404(visitor_id)
    
    # Remove them from the database session and save
    db.session.delete(visitor_to_delete)
    db.session.commit()
    
    # Send the user right back to the guestbook page
    return redirect(url_for('greet'))

@app.route("/products")
def products():
    # Simulating a database pull of our product inventory
    catalog = [
        {
            "id": 1,
            "name": "Quantum-X Mechanical Keyboard",
            "price": 149.99,
            "description": "Hot-swappable switches with dynamic RGB backlighting and an aluminum frame.",
            "image": "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=500&auto=format&fit=crop&q=60",
            "in_stock": True
        },
        {
            "id": 2,
            "name": "AeroStream Wireless Mouse",
            "price": 89.95,
            "description": "Ultra-lightweight ergonomic mouse boasting an 80-hour battery life and 26K DPI sensor.",
            "image": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop&q=60",
            "in_stock": True
        },
        {
            "id": 3,
            "name": "Horizon 34\" Ultrawide Monitor",
            "price": 450.00,
            "description": "1440p curved display with 165Hz refresh rate for ultimate productivity and immersion.",
            "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500&auto=format&fit=crop&q=60",
            "in_stock": False # Out of stock item!
        }
    ]
    return render_template("products.html", items=catalog)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Store hashes, NEVER plain text!

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists AND password matches the stored mathematical hash
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('greet'))
        else:
            return "Invalid username or password. Please try again."
            
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Check if username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "That username is already taken. Choose another one!"
            
        # If available, scramble the password and save the new user
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log them in automatically after signing up, then send to guestbook
        login_user(new_user)
        return redirect(url_for('greet'))
        
    return render_template("signup.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
  # This tells Flask to automatically build the database file 
  # if it doesn't see it when the server starts up!
  with app.app_context():
    db.create_all()

  app.run(debug=True)