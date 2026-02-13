from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    players = db.relationship('Player', backref='game', lazy=True)
    rounds = db.relationship('Round', backref='game', lazy=True)
    config = db.relationship('ContractConfig', backref='game', uselist=False, lazy=True)

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
    miserie_participants = db.Column(db.Text, nullable=True)  # JSON: {player_id: result} for multi-player Miserie
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    scores = db.relationship('Score', backref='round', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    points_change = db.Column(db.Integer, nullable=False)
    current_total = db.Column(db.Integer, nullable=False)

class ContractConfig(db.Model):
    """Configuration for contract points and trick limits per game."""
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False, unique=True)
    
    # Contract points - distinguish between Vraag with/without partner
    vraag_partner_points = db.Column(db.Integer, default=2, nullable=False)  # Vraag with partner (2v2)
    vraag_solo_points = db.Column(db.Integer, default=2, nullable=False)     # Vraag alone (1v3)
    troel_points = db.Column(db.Integer, default=2, nullable=False)
    abondance_points = db.Column(db.Integer, default=5, nullable=False)
    solo_points = db.Column(db.Integer, default=13, nullable=False)
    miserie_points = db.Column(db.Integer, default=10, nullable=False)
    grote_miserie_points = db.Column(db.Integer, default=20, nullable=False)
    
    # Trick limits - separate for Vraag with/without partner
    vraag_partner_tricks_won_max = db.Column(db.Integer, default=5, nullable=False)
    vraag_partner_tricks_lost_max = db.Column(db.Integer, default=8, nullable=False)
    vraag_solo_tricks_won_max = db.Column(db.Integer, default=5, nullable=False)
    vraag_solo_tricks_lost_max = db.Column(db.Integer, default=8, nullable=False)
    troel_tricks_won_max = db.Column(db.Integer, default=5, nullable=False)
    troel_tricks_lost_max = db.Column(db.Integer, default=8, nullable=False)
    abondance_tricks_won_max = db.Column(db.Integer, default=4, nullable=False)
    abondance_tricks_lost_max = db.Column(db.Integer, default=9, nullable=False)
