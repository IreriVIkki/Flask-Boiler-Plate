from datetime import datetime
from dtserver import db, ma


# Video Model
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(20), nullable=False, unique=True)
    uploaded = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey(
        'account.id'), nullable=False)

    def __repr__(self):
        return f"Video (id: {self.id}, video_id: {self.video_id}, uploaded: {self.uploaded}, account: {self.account_id} )"


# Video Schema
class VideoSchema(ma.ModelSchema):
    class Meta:
        model = Video


# Init Video schema
video_schema = VideoSchema(strict=True)
videos_schema = VideoSchema(many=True, strict=True)


# Account Model
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel_name = db.Column(db.String(50), nullable=False)
    channel_Id = db.Column(db.String(50), nullable=False)
    account_avatar = db.Column(db.String(200))
    api_key = db.Column(db.String(200), unique=True, nullable=False)
    api_secret = db.Column(db.String(200), unique=True, nullable=False)
    user_name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    search_order = db.Column(db.String(20), nullable=False)
    search_terms = db.Column(db.String(2000), nullable=False)
    queue_status = db.Column(db.Boolean(), default=True, nullable=False)
    current = db.Column(db.Boolean(), default=False, nullable=False)
    video_duration_remaining = db.Column(db.Integer, nullable=False, default=0)
    upload_videos_remaining = db.Column(db.Integer, nullable=False, default=0)
    video_size_remaining = db.Column(db.Float, nullable=False, default=0.0)
    videos = db.relationship('Video', backref='account', lazy=True)

    def __repr__(self):
        return f"Account( channel_name: {self.channel_name}, hours uploaded:{self.video_duration_remaining}, videos uploaded: {self.upload_videos_remaining}, search_ids: {self.search_ids})"


# Account Schema
class AccountSchema(ma.ModelSchema):
    class Meta:
        model = Account


# Init schemas
account_schema = AccountSchema(strict=True)
accounts_schema = AccountSchema(many=True, strict=True)
