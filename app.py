from flask import send_file
from io import BytesIO
from os import abort
from boto3.dynamodb.conditions import Key
from flask import Flask, request, redirect, render_template, flash, url_for, session
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 's3890097'

# Initialize DynamoDB clients
dynamodb = boto3.resource('dynamodb', region_name = 'us-east-1')
login_table = dynamodb.Table('login')
music_table = dynamodb.Table('music')
subscription_table = dynamodb.Table('subscriptions')

@app.route('/')
def home():
    if 'email' not in session:
        return redirect(url_for('login'))
    user_email = session['email']
    subscriptions = get_user_subscriptions(user_email)
    return render_template('main.html', username=session.get('username'), subscriptions=subscriptions)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            response = login_table.get_item(
                Key={'email': email}
            )
            user = response.get('Item')
            if user and user['password'] == password:
                session['email'] = user['email']
                session['username'] = user.get('user_name') 
                return redirect(url_for('home'))
            else:
                flash('Email or password is invalid', 'error')
        except ClientError as e:
            flash(f'AWS Error: {e.response["Error"]["Message"]}', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    # Redirect to the login page
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        try:
            response = login_table.get_item(
                Key={'email': email}
            )
            user = response.get('Item')
            if user:
                flash('The email already exists', 'error')
            else:
                login_table.put_item(
                    Item={
                        'email': email,
                        'user_name': username,
                        'password': password
                    }
                )
                return redirect(url_for('login'))
        except ClientError as e:
            flash(f'AWS Error: {e.response["Error"]["Message"]}', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('register.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    user_email = session.get('email')
    if not user_email:
        flash("You must be logged in to subscribe.", "error")
        return redirect(url_for('login'))

    music_title = request.form.get('music_title')
    artist = request.form.get('artist')
    image_url = request.form.get('image_url')
    year = request.form.get('year')
    unwanted_prefix = "https://artistimagesbucket.s3.amazonaws.com/"
    if image_url.startswith(unwanted_prefix):
        image_url = image_url.replace(unwanted_prefix, "", 1)  
    # Check if already subscribed
    try:
        response = subscription_table.get_item(
            Key={
                'user_email': user_email,
                'music_title': music_title
            }
        )
        if 'Item' in response:
            flash("You are already subscribed to this music!", "info")
            return redirect(url_for('home'))

        # Save subscription to subscriptions
        subscription_table.put_item(
            Item={
                'user_email': user_email,
                'music_title': music_title,
                'artist': artist,
                'image_url': image_url,
                'year': year  
            }
        )
        flash("Successfully subscribed to the music!", "success")
    except ClientError as e:
        flash(f"Failed to subscribe due to {e.response['Error']['Message']}", "error")

    return redirect(url_for('home'))

@app.route('/remove-subscription', methods=['POST'])
def remove_subscription():
    user_email = session.get('email')
    if not user_email:
        flash("You must be logged in to perform this action.", "error")
        return redirect(url_for('login'))

    music_title = request.form.get('music_title')

    try:
        # Delete the subscription item
        response = subscription_table.delete_item(
            Key={
                'user_email': user_email,
                'music_title': music_title
            }
        )
        flash("Subscription successfully removed.", "success")
    except ClientError as e:
        flash(f"Failed to remove subscription: {e.response['Error']['Message']}", "error")

    return redirect(url_for('home'))




@app.route('/query', methods=['POST'])
def query():
    title = request.form.get('title', '').strip().lower()
    artist = request.form.get('artist', '').strip().lower()
    year = request.form.get('year', '').strip()

    try:
        response = music_table.scan()
        music_items = response['Items']
        filtered_music_items = []
        for item in music_items:
            if (not title or item['title'].lower() == title) and \
               (not artist or item['artist'].lower() == artist) and \
               (not year or item['year'] == year):
                artist_name = item['artist'].replace(' ', '')
                item['img_url'] = f"https://artistimagesbucket.s3.amazonaws.com/{artist_name}.jpg"
                filtered_music_items.append(item)

        if not filtered_music_items:
            flash("No results found. Please try different criteria.", "info")

        return render_template('main.html', username=session.get('username'), subscriptions=get_user_subscriptions(session['email']), results=filtered_music_items)
    except ClientError as e:
        flash(f"Error querying music: {e.response['Error']['Message']}", "error")
        return redirect(url_for('home'))




def get_user_subscriptions(email):
    try:
        response = subscription_table.query(KeyConditionExpression=Key('user_email').eq(email))
        subscriptions = response.get('Items', [])
        for subscription in subscriptions:
            artist_name = subscription['artist'].replace(' ', '')
            subscription['image_url'] = f"https://artistimagesbucket.s3.amazonaws.com/{artist_name}.jpg"
        return subscriptions
    except ClientError as e:
        flash(f"Unable to retrieve subscriptions: {e.response['Error']['Message']}", "error")
        return []


if __name__ == '__main__':
    app.run(debug=True)

