from flask import request, jsonify, Response
from dtserver import app, db, daily_motion
from .models import Account, Video, account_schema, accounts_schema, video_schema, videos_schema
import os
from pytube import YouTube
# from pytube.__main__ import YouTube
from textblob import TextBlob


@app.route('/')
def home():
    return Response('working so far')


# get all accounts
@app.route('/api/gets_all_accounts', methods=['GET'])
def gets_all_accounts():
    all_accounts = Account.query.all()
    result = accounts_schema.dump(all_accounts)
    return jsonify(result.data)


# get all accounts
@app.route('/api/get_all_video_ids', methods=['GET'])
def gets_all_videos():
    all_videos = Video.query.with_entities(Video.video_id).all()
    result = videos_schema.dump(all_videos)
    return jsonify(result.data)


@app.route('/api/get_un_uploaded_account_videos', methods=['GET'])
def get_account_videos():
    account_id = int(request.args['account_id'])
    all_videos = Video.query.filter_by(
        account_id=account_id, uploaded=False).with_entities(Video.video_id)
    result = videos_schema.dump(all_videos)
    return jsonify(result.data)


# create new account
@app.route('/api/create_new_account', methods=['POST'])
def create_new_account():
    api_key = request.get_json()['apiKey']
    api_secret = request.get_json()['apiSecret']
    password = request.get_json()['channelPassword']
    user_name = request.get_json()['channelUsername']
    search_order = request.get_json()['searchOrder']
    search_terms = request.get_json()['searchTerms']

    # Check that channel does not exist in db
    account = Account.query.filter_by(user_name=user_name).first()

    # Respond with appropriate message if it exists
    if account != None:
        return jsonify({"success": False, "message": f"Account with username {user_name} already exists"})

    # Else Create a new account
    else:
        daily_motion.set_grant_type('password', api_key=api_key, api_secret=api_secret, scope=[
                                    'userinfo'], info={'username': user_name, 'password': password})

        channel = daily_motion.get(
            '/me', {'fields': 'id,username,screenname,limits'})

        account_avatar = daily_motion.get(
            f'/user/{channel["id"]}', {'fields': 'avatar_60_url'})

        video_duration = channel['limits']['video_duration']
        video_size = channel['limits']['video_size']

        # new account
        new_account = Account(channel_Id=channel['id'], account_avatar=account_avatar['avatar_60_url'], api_key=api_key, api_secret=api_secret, password=password, channel_name=channel['screenname'], user_name=user_name, search_order=search_order, search_terms=','.join(search_terms),
                              queue_status=False, current=False, video_duration_remaining=video_duration, upload_videos_remaining=10, video_size_remaining=video_size)

        db.session.add(new_account)
        db.session.commit()

        # Respond with a success message and channel name which will be saved to state as newly created channel
        return jsonify({"success": True, "message": f"Account with username {user_name} created successfully", "accountId": new_account.id})


# update account
@app.route('/api/update_account', methods=['PUT'])
def update_account():
    account_id = int(request.args['account_id'])
    account = Account.query.get(account_id)

    body = request.get_json()

    try:
        if account.current != body['isCurrent']:
            Account.query.filter_by(current=True).update(
                {Account.current: False})
            account.current = body['isCurrent']
    except:
        pass

    try:
        for video_id in body['searchIds']:
            new_video = Video(video_id=video_id,
                              account_id=account_id, uploaded=False)
            db.session.add(new_video)
    except:
        # db.session.rollback()
        pass

    try:
        account.queue_status = body['isQueued']
    except:
        pass

    try:
        account.search_terms = ','.join(body['searchTerms'])
    except:
        pass

    try:
        account.search_order = body['searchOrder']
    except:
        pass

    db.session.commit()

    return jsonify({"success": True})


# get account information
@app.route('/api/get_account_info', methods=['GET'])
def get_account():
    account_id = int(request.args['account_id'])
    account = Account.query.get(account_id)

    # Authenticate Dailymotion
    scope = ['userinfo', 'read', 'read_insights']
    info = {'username': account.user_name, 'password': account.password}
    daily_motion.set_grant_type('password', api_key=account.api_key,
                                api_secret=account.api_secret, scope=scope, info=info)

    daily_motion_user = daily_motion.get('/me', {'fields': 'id'})

    daily_motion_user_info = daily_motion.get(
        f'/user/{daily_motion_user["id"]}', {'fields': 'followers_total,following_total,avatar_60_url,revenues_video_last_day,revenues_video_last_month,revenues_video_total,screenname,username,url,videos_total,views_total'})

    return jsonify({"info": daily_motion_user_info, "upload": {"id": account.id, "search_order": account.search_order, "search_terms": account.search_terms, "queue_status": account.queue_status, "current": account.current, "minutes_remaining": account.video_duration_remaining, "videos_remaining": account.upload_videos_remaining}})


# delete account information
@app.route('/api/delete_account', methods=['DELETE'])
def delete_account():
    account_id = int(request.args['account_id'])
    Account.query.filter_by(id=account_id).delete()
    db.session.commit()
    return jsonify({"success": True, "account": account_id})


@app.route('/api/download_video', methods=['POST'])
def download_video():
    # Extract request data
    video_id = request.get_json()['videoId']
    video_title = request.get_json()['title']
    old_file_path = request.get_json()['filePath']

    # Delete previously uploaded video
    try:
        print(old_file_path)
        os.remove(old_file_path)
    except:
        pass

    # Init
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    global response
    video_name = video_title.replace(' ', '')
    file_path = f'{os.getcwd()}/{video_name}.mp4'

    # Execute
    try:
        yt = YouTube(video_url)
        if yt.length > "900":
            video = Video.query.filter_by(video_id=video_id).delete()
            db.session.commit()
            response = {"success": False, "message": "Video too long"}
        else:
            video = yt.streams.filter(subtype='mp4').first()
            try:
                video.download(filename=video_name)
                response = {"success": True, "file_path": file_path, "message": "Download successful"}
            except:
                pass
            else:
                video.download(filename=video_name)
                pass
                response = {"success": True, "file_path": file_path, "message": "Download successful"}
    except:
        video = Video.query.filter_by(video_id=video_id).delete()
        db.session.commit()
        response = {"success": False, "message": "Download Error"}

    return jsonify(response)


@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    # Extract request data
    account_id = int(request.args['account_id'])
    file_path = request.get_json()['filePath']
    video_id = request.get_json()['videoId']

    # Init
    account = Account.query.get(account_id)
    global response

    # Authenticate DailyMotion
    scope = ['manage_videos', 'manage_playlists', 'userinfo']
    info = {'username': account.user_name, 'password': account.password}
    daily_motion.set_grant_type('password', api_key=account.api_key,
                                api_secret=account.api_secret, scope=scope, info=info)


    # Execute
    try:
        publish_url = daily_motion.upload(file_path)
        response = {"success": True, "publish_url": publish_url, "message" : "Upload Successful"}
    except:
        video = Video.query.filter_by(video_id=video_id).delete()
        db.session.commit()
        response = {"success": False, "message": "Upload Failed"}

    # delete the file from the database after uploading
    os.remove(file_path)
    return jsonify(response)


@app.route('/api/publish_video', methods=['POST'])
def publish_video():
    # Extract request data
    account_id = int(request.args['account_id'])
    video_id = request.get_json()['videoId']
    publish_url = request.get_json()['publishUrl']
    title = request.get_json()['title']
    tags = request.get_json()['tags']
    description = request.get_json()['description']
    thumbnail_url = request.get_json()['thumbnailUrl']

    # Init
    account = Account.query.get(account_id)
    global response

    # Authenticate DailyMotion
    scope = ['manage_videos', 'userinfo']
    info = {'username': account.user_name, 'password': account.password}
    daily_motion.set_grant_type('password', api_key=account.api_key,
                                api_secret=account.api_secret, scope=scope, info=info)


    # Execute
    desc_tags = TextBlob(description.replace('  ', ' '))
    tags = tags + list(desc_tags.noun_phrases)
    all_tags = ','.join(tags[:50])
    upload_object = {'url': publish_url,'published': 'true','channel': 'fun','title': title,'description': description,'tags': all_tags,'thumbnail_url': thumbnail_url}

    try:
        # Publish video
        daily_motion.post('/me/videos', upload_object)
        # get channel limits
        channel = daily_motion.get('/me', {'fields': 'limits'})
        # update channel limits
        video_duration = channel['limits']['video_duration']
        video_size = channel['limits']['video_size']
        account.video_duration_remaining = video_duration
        account.video_size_remaining = video_size
        account.upload_videos_remaining -= 1
        # Update video upload status
        video = Video.query.filter_by(video_id=video_id).first()
        video.uploaded = True
        # Commit all the changes to the database
        db.session.commit()
        response = {"success": True, "message": "Video Published Successfully"}
    except:
        video = Video.query.filter_by(video_id=video_id).delete()
        db.session.commit()
        response = {"success": False, "message": "Publish Failed"}

    return jsonify(response)
