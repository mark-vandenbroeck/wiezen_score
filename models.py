from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    players = db.relationship('Player', backref='game', lazy=True)
    rounds = db.relationship('Round', backref='game', lazy=True)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    scores = db.relationship('Score', backref='player', lazy=True)

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    contract_type = db.Column(db.String(50), nullable=False) # e.g., 'Vraag', 'Miserie', 'Abondance'
    result = db.Column(db.String(50), nullable=False) # e.g., 'Gewonnen', 'Verloren'
    trump_suit = db.Column(db.String(20), nullable=True) # New: Trump suit
    tricks = db.Column(db.Integer, nullable=True) # Number of tricks won
    
    dealer_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    sitter_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    main_player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=True) # Partner for 'Vraag'
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    scores = db.relationship('Score', backref='round', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    points_change = db.Column(db.Integer, nullable=False)
    current_total = db.Column(db.Integer, nullable=False)
