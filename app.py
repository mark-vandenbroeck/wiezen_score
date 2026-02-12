from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, Game, Player, Round, Score
import os

app = Flask(__name__)
# Use an absolute path for the database file to avoid issues
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'wiezen.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Use an absolute path for the database file to avoid issues
# Note: basedir is already defined above
db_path = os.path.join(basedir, 'wiezen.db')

def init_db():
    with app.app_context():
        db.create_all()
        # Optional: Add initial data or logging here

# Ensure DB exists on startup
if not os.path.exists(db_path):
    init_db()

@app.before_request
def ensure_db_exists():
    # Check if DB file was deleted while running
    if not os.path.exists(db_path):
        init_db()

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Check if there is an active game
    active_game = Game.query.filter_by(is_active=True).first()
    if active_game:
        players = sorted(active_game.players, key=lambda p: p.id)
        # Get latest scores for each player
        current_scores = {}
        for player in players:
            last_score = Score.query.filter_by(player_id=player.id).order_by(Score.id.desc()).first()
            current_scores[player.id] = last_score.current_total if last_score else 0
        
        # Prepare history and current dealer
        raw_rounds = Round.query.filter_by(game_id=active_game.id).order_by(Round.id.desc()).all()
        history = []
        
        # Calculate current dealer (based on next round number)
        num_players = len(players)
        next_round_num = len(active_game.rounds) + 1
        current_dealer_index = (next_round_num - 1) % num_players
        current_dealer_id = players[current_dealer_index].id
        
        # In 5-player game, dealer sits out
        current_sitter_id = current_dealer_id if num_players == 5 else None
        
        for r in raw_rounds:
            # Calculate dealer for this round
            round_dealer_index = (r.round_number - 1) % num_players
            round_dealer_id = players[round_dealer_index].id # Assuming players order is static/sorted by ID
            round_sitter_id = round_dealer_id if num_players == 5 else None
            
            round_data = {
                'round_number': r.round_number,
                'contract_type': r.contract_type,
                'result': r.result,
                'tricks': r.tricks,
                'trump_suit': r.trump_suit,
                'scores': {},
                'dealer_id': round_dealer_id,
                'sitter_id': round_sitter_id
            }
            # Efficiently map scores for this round
            for s in r.scores:
                round_data['scores'][s.player_id] = s.points_change
            history.append(round_data)

        return render_template('index.html', game=active_game, players=players, scores=current_scores, rounds=history, current_dealer_id=current_dealer_id, current_sitter_id=current_sitter_id)
    
    return render_template('setup.html')

@app.route('/game/start', methods=['POST'])
@app.route('/game/start', methods=['POST'])
def start_game():
    player_names = [name for name in request.form.getlist('player_name') if name.strip()]
    if not player_names:
        player_names = ['Jan', 'Piet', 'Joris', 'Korneel'] # Defaults
        
    if len(player_names) < 4 or len(player_names) > 5:
        return "Error: 4 or 5 players are required", 400
    
    # Deactivate any existing active games
    active_games = Game.query.filter_by(is_active=True).all()
    for g in active_games:
        g.is_active = False
    
    new_game = Game()
    db.session.add(new_game)
    db.session.commit()
    
    for name in player_names:
        player = Player(name=name, game_id=new_game.id)
        db.session.add(player)
        db.session.commit() # Commit each to get ID
        
        # Initial score 0
        initial_score = Score(round_id=0, player_id=player.id, points_change=0, current_total=0)
        # Need a dummy round 0 or handle this differently? 
        # Actually, let's just use 0 as base and no specific round entry needed for init if we handle it in logic
        # But for consistency, let's just say we don't add a score entry yet, 0 is implied.
    
    return redirect(url_for('index'))

@app.route('/round/add', methods=['POST'])
def add_round():
    active_game = Game.query.filter_by(is_active=True).first()
    if not active_game:
        return redirect(url_for('index'))

    # Helper to find player by name or ID from form
    # Assuming form sends player IDs
    
    contract = request.form.get('contract')
    main_player_id = request.form.get('main_player')
    partner_id = request.form.get('partner_id')
    result = request.form.get('result') # 'won' or 'lost'
    tricks = int(request.form.get('tricks', 0))
    
    # Basic Wiezen scoring rules (simplified for now, can be expanded)
    # This is a placeholder for the actual complex logic of Wiezen
    
    # Validation: Partner cannot be Main Player
    if partner_id and partner_id == main_player_id:
        return "Error: Speler en partner mogen niet dezelfde persoon zijn.", 400
    # Validation: Extra Tricks Limit
    if contract in ['Vraag', 'Troel']:
        limit = 5 if result == 'Gewonnen' else 8
        if tricks > limit:
             return f"Error: Maximaal {limit} extra slagen bij {contract} ({result}).", 400
    
    if contract == 'Abondance':
        limit = 4 if result == 'Gewonnen' else 9
        if tricks > limit:
            return f"Error: Maximaal {limit} extra slagen bij Abondance ({result}).", 400

    if contract in ['Miserie', 'Grote Miserie', 'Solo'] and tricks > 0:
        return f"Error: Geen extra slagen toegestaan bij {contract}.", 400
    
    # Validation: Troel must have a partner
    if contract == 'Troel' and not partner_id:
        return "Error: Bij Troel moet er altijd een partner gekozen worden.", 400

    # Validation: Trump is mandatory for non-Miserie contracts
    # Trump is fetched later, so get it here or move fetch up.
    trump_suit = request.form.get('trump_suit')
    if contract in ['Vraag', 'Troel', 'Abondance', 'Solo'] and not trump_suit:
        return "Error: Kies een troefkleur (Harten, Ruiten, Klaveren of Schoppen).", 400

    base_points = 0
    if contract == 'Vraag':
        base_points = 2
    elif contract == 'Troel':
        base_points = 2
    elif contract == 'Abondance':
        base_points = 5
    elif contract == 'Miserie':
        base_points = 10
    elif contract == 'Grote Miserie':
        base_points = 20
    elif contract == 'Solo':
        base_points = 13
    
    points = base_points + tricks # Simplified
    
    # Determine sitter (dealer of this round)
    players = active_game.players
    num_players = len(players)
    new_round_num = len(active_game.rounds) + 1
    round_dealer_index = (new_round_num - 1) % num_players
    round_dealer_id = players[round_dealer_index].id
    sitter_id = round_dealer_id if num_players == 5 else None

    # Create new round
    trump_suit = request.form.get('trump_suit') if contract in ['Vraag', 'Abondance', 'Troel', 'Solo'] else None
    
    new_round = Round(
        game_id=active_game.id,
        round_number=new_round_num,
        dealer_id=round_dealer_id,
        sitter_id=sitter_id,
        contract_type=contract,
        main_player_id=main_player_id,
        partner_id=partner_id if partner_id else None,
        result=result,
        trump_suit=trump_suit,
        tricks=tricks
    )
    db.session.add(new_round)
    db.session.commit()
    
    # Calculate scores for each player
    num_players = len(players)
    
    # Determine sitter (dealer of this round)
    # round_number is already active_game.rounds length + 1, so new_round.round_number
    round_dealer_index = (new_round.round_number - 1) % num_players
    round_dealer_id = players[round_dealer_index].id
    sitter_id = round_dealer_id if num_players == 5 else None

    total_change = points if result == 'Gewonnen' else -points
    
    # Calculate scores
    score_changes = {p.id: 0 for p in players}

    if contract in ['Miserie', 'Grote Miserie']:
        # Base value
        base_val = 20 if contract == 'Grote Miserie' else 10
        
        # Check for each player if they played
        for player in players:
            if player.id == sitter_id:
                continue
                
            # Check form for this player's involvement
            # Expecting input name="miserie_play_{player.id}" (checkbox)
            # and name="miserie_result_{player.id}" (value 'Gewonnen' or 'Verloren')
            if request.form.get(f'miserie_play_{player.id}'):
                p_result = request.form.get(f'miserie_result_{player.id}')
                p_points = base_val # Fixed points for Miserie
                
                if p_result == 'Gewonnen':
                    # Player wins: receives base_val from each opponent
                    # Opponents count = num_active_players - 1
                    num_active = num_players - (1 if sitter_id else 0)
                    win_amount = p_points * (num_active - 1)
                    
                    score_changes[player.id] += win_amount
                    # Each opponent loses p_points
                    for opponent in players:
                        if opponent.id != player.id and opponent.id != sitter_id:
                            score_changes[opponent.id] -= p_points
                else: # lost
                    # Player loses: pays base_val to each opponent
                    num_active = num_players - (1 if sitter_id else 0)
                    loss_amount = p_points * (num_active - 1)
                    
                    score_changes[player.id] -= loss_amount
                    # Each opponent wins p_points
                    for opponent in players:
                        if opponent.id != player.id and opponent.id != sitter_id:
                            score_changes[opponent.id] += p_points

    else: # Standard contracts
        for player in players:
            change = 0
            is_sitter = (player.id == sitter_id)
            
            if is_sitter:
                change = 0 # Sitter doesn't play
            else:
                is_main = str(player.id) == main_player_id
                is_partner = str(player.id) == partner_id if partner_id else False

                if partner_id: 
                    if is_main or is_partner:
                        change = total_change # Winners get points
                    else:
                        change = -total_change # Losers lose points
                else: # 1 vs 3
                    if is_main:
                        change = total_change * 3 # Winner gets from all 3
                    else:
                        change = -total_change # Losers pay winner
            score_changes[player.id] = change

    for player in players:
        change = score_changes[player.id]
        last_score = Score.query.filter_by(player_id=player.id).order_by(Score.id.desc()).first()
        current_total = (last_score.current_total if last_score else 0) + change
        
        new_score = Score(
            round_id=new_round.id,
            player_id=player.id,
            points_change=change,
            current_total=current_total
        )
        db.session.add(new_score)
        
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/game/end', methods=['POST'])
def end_game():
    active_game = Game.query.filter_by(is_active=True).first()
    if active_game:
        active_game.is_active = False
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
