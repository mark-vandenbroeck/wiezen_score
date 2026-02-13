from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import db, Game, Player, Round, Score, ContractConfig
import os

app = Flask(__name__)
# Use an absolute path for the database file to avoid issues
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'wiezen.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

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

def get_contract_config(game_id):
    """Get contract config for game, with fallback to defaults for backwards compatibility."""
    config = ContractConfig.query.filter_by(game_id=game_id).first()
    if not config:
        # Return object with default values for backwards compatibility
        class DefaultConfig:
            vraag_partner_points = 2
            vraag_solo_points = 2
            troel_points = 2
            abondance_points = 5
            solo_points = 13
            miserie_points = 10
            grote_miserie_points = 20
            vraag_partner_tricks_won_max = 5
            vraag_partner_tricks_lost_max = 8
            vraag_solo_tricks_won_max = 5
            vraag_solo_tricks_lost_max = 8
            troel_tricks_won_max = 5
            troel_tricks_lost_max = 8
            abondance_tricks_won_max = 4
            abondance_tricks_lost_max = 9
        return DefaultConfig()
    return config

def get_contract_points(config, contract_type, has_partner=False):
    """Get points for a specific contract type."""
    if contract_type == 'Vraag':
        return config.vraag_partner_points if has_partner else config.vraag_solo_points
    elif contract_type == 'Troel':
        return config.troel_points
    elif contract_type == 'Abondance':
        return config.abondance_points
    elif contract_type == 'Solo':
        return config.solo_points
    elif contract_type == 'Miserie':
        return config.miserie_points
    elif contract_type == 'Grote Miserie':
        return config.grote_miserie_points
    return 0

def get_trick_limits(config, contract_type, result, has_partner=False):
    """Get trick limits for a specific contract type and result."""
    if contract_type == 'Vraag':
        if has_partner:
            return config.vraag_partner_tricks_won_max if result == 'Gewonnen' else config.vraag_partner_tricks_lost_max
        else:
            return config.vraag_solo_tricks_won_max if result == 'Gewonnen' else config.vraag_solo_tricks_lost_max
    elif contract_type == 'Troel':
        return config.troel_tricks_won_max if result == 'Gewonnen' else config.troel_tricks_lost_max
    elif contract_type == 'Abondance':
        return config.abondance_tricks_won_max if result == 'Gewonnen' else config.abondance_tricks_lost_max
    return 0

@app.route('/')
def index():
    # Check if there is an active game
    active_game = Game.query.filter_by(is_active=True).first()
    if active_game:
        players = sorted(active_game.players, key=lambda p: p.id)
        
        # Safety check: if no players, redirect to setup
        if not players:
            active_game.is_active = False
            db.session.commit()
            return render_template('setup.html')
        
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
                'id': r.id,
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
    
    # Create contract configuration for this game
    # Check if there's a pending config in session
    from flask import session
    pending_config = session.pop('pending_config', None)
    
    if pending_config:
        # Apply the pending configuration
        game_config = ContractConfig(
            game_id=new_game.id,
            vraag_partner_points=pending_config.get('vraag_partner_points', 2),
            vraag_solo_points=pending_config.get('vraag_solo_points', 2),
            troel_points=pending_config.get('troel_points', 2),
            abondance_points=pending_config.get('abondance_points', 5),
            solo_points=pending_config.get('solo_points', 13),
            miserie_points=pending_config.get('miserie_points', 10),
            grote_miserie_points=pending_config.get('grote_miserie_points', 20),
            vraag_partner_tricks_won_max=pending_config.get('vraag_partner_tricks_won_max', 5),
            vraag_partner_tricks_lost_max=pending_config.get('vraag_partner_tricks_lost_max', 8),
            vraag_solo_tricks_won_max=pending_config.get('vraag_solo_tricks_won_max', 5),
            vraag_solo_tricks_lost_max=pending_config.get('vraag_solo_tricks_lost_max', 8),
            troel_tricks_won_max=pending_config.get('troel_tricks_won_max', 5),
            troel_tricks_lost_max=pending_config.get('troel_tricks_lost_max', 8),
            abondance_tricks_won_max=pending_config.get('abondance_tricks_won_max', 4),
            abondance_tricks_lost_max=pending_config.get('abondance_tricks_lost_max', 9)
        )
    else:
        # Use default configuration
        game_config = ContractConfig(game_id=new_game.id)
    
    db.session.add(game_config)
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
    # Get contract configuration for this game
    config = get_contract_config(active_game.id)
    has_partner = bool(partner_id)
    
    # Validation: Extra Tricks Limit (using configurable limits)
    if contract in ['Vraag', 'Troel']:
        limit = get_trick_limits(config, contract, result, has_partner)
        if tricks > limit:
             return f"Error: Maximaal {limit} extra slagen bij {contract} ({result}).", 400
    
    if contract == 'Abondance':
        limit = get_trick_limits(config, contract, result)
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

    # Get base points from configuration (supports Vraag with/without partner)
    base_points = get_contract_points(config, contract, has_partner)
    
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
        # Use configurable base value
        base_val = get_contract_points(config, contract)
        
        # Store participant data for future recalculation
        participants_data = {}
        
        # Check for each player if they played
        for player in players:
            if player.id == sitter_id:
                continue
                
            # Check form for this player's involvement
            # Expecting input name="miserie_play_{player.id}" (checkbox)
            # and name="miserie_result_{player.id}" (value 'Gewonnen' or 'Verloren')
            if request.form.get(f'miserie_play_{player.id}'):
                p_result = request.form.get(f'miserie_result_{player.id}')
                participants_data[str(player.id)] = p_result
                
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
        
        # Store participant data in round for recalculation
        import json
        new_round.miserie_participants = json.dumps(participants_data)
        db.session.commit()

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

def recalculate_scores_from_round(game_id, start_round_number=1):
    """
    Recalculate all scores starting from a specific round number.
    This is used after editing or deleting rounds to ensure score integrity.
    """
    game = Game.query.get(game_id)
    if not game:
        return
    
    players = sorted(game.players, key=lambda p: p.id)
    
    # Delete all scores for rounds >= start_round_number
    rounds_to_recalc = Round.query.filter(
        Round.game_id == game_id,
        Round.round_number >= start_round_number
    ).order_by(Round.round_number).all()
    
    for round_obj in rounds_to_recalc:
        Score.query.filter_by(round_id=round_obj.id).delete()
    
    # Get baseline scores from previous round
    baseline_scores = {}
    if start_round_number > 1:
        prev_round = Round.query.filter(
            Round.game_id == game_id,
            Round.round_number == start_round_number - 1
        ).first()
        if prev_round:
            for score in prev_round.scores:
                baseline_scores[score.player_id] = score.current_total
    
    # If no baseline, start from 0
    for player in players:
        if player.id not in baseline_scores:
            baseline_scores[player.id] = 0
    
    # Recalculate scores for each round
    for round_obj in rounds_to_recalc:
        calculate_and_save_scores(round_obj, players, baseline_scores)
    
    db.session.commit()

def calculate_and_save_scores(round_obj, players, baseline_scores):
    """Calculate and save scores for a specific round."""
    num_players = len(players)
    sitter_id = round_obj.sitter_id
    
    # Calculate score changes based on contract type
    score_changes = {p.id: 0 for p in players}
    
    contract = round_obj.contract_type
    result = round_obj.result
    tricks = round_obj.tricks or 0
    main_player_id = str(round_obj.main_player_id) if round_obj.main_player_id else None
    partner_id = str(round_obj.partner_id) if round_obj.partner_id else None
    
    # Get contract configuration for this game
    config = get_contract_config(round_obj.game_id)
    has_partner = bool(partner_id)
    
    # Calculate base points using configuration
    base_points = get_contract_points(config, contract, has_partner)
    
    points = base_points + tricks
    total_change = points if result == 'Gewonnen' else -points
    
    if contract in ['Miserie', 'Grote Miserie']:
        # Use stored participant data if available
        if round_obj.miserie_participants:
            import json
            participants_data = json.loads(round_obj.miserie_participants)
            # Use configurable points for Miserie
            base_val = get_contract_points(config, contract)
            
            # Recalculate scores based on stored participant data
            for player_id_str, p_result in participants_data.items():
                player_id = int(player_id_str)
                p_points = base_val
                
                if p_result == 'Gewonnen':
                    # Player wins: receives base_val from each opponent
                    num_active = num_players - (1 if sitter_id else 0)
                    win_amount = p_points * (num_active - 1)
                    
                    score_changes[player_id] += win_amount
                    # Each opponent loses p_points
                    for player in players:
                        if player.id != player_id and player.id != sitter_id:
                            score_changes[player.id] -= p_points
                else:  # Verloren
                    # Player loses: pays base_val to each opponent
                    num_active = num_players - (1 if sitter_id else 0)
                    loss_amount = p_points * (num_active - 1)
                    
                    score_changes[player_id] -= loss_amount
                    # Each opponent wins p_points
                    for player in players:
                        if player.id != player_id and player.id != sitter_id:
                            score_changes[player.id] += p_points
        else:
            # Fallback for old rounds without participant data
            # Set all scores to 0 - cannot recalculate without data
            pass
    else:
        for player in players:
            change = 0
            is_sitter = (player.id == sitter_id)
            
            if is_sitter:
                change = 0
            else:
                is_main = str(player.id) == main_player_id
                is_partner = str(player.id) == partner_id if partner_id else False
                
                if partner_id:
                    if is_main or is_partner:
                        change = total_change
                    else:
                        change = -total_change
                else:  # 1 vs 3
                    if is_main:
                        change = total_change * 3
                    else:
                        change = -total_change
            score_changes[player.id] = change
    
    # Save scores
    for player in players:
        change = score_changes[player.id]
        current_total = baseline_scores.get(player.id, 0) + change
        
        new_score = Score(
            round_id=round_obj.id,
            player_id=player.id,
            points_change=change,
            current_total=current_total
        )
        db.session.add(new_score)
        baseline_scores[player.id] = current_total

@app.route('/round/undo', methods=['POST'])
def undo_round():
    """Undo (delete) the last round."""
    active_game = Game.query.filter_by(is_active=True).first()
    if not active_game:
        return redirect(url_for('index'))
    
    # Get the last round
    last_round = Round.query.filter_by(game_id=active_game.id).order_by(Round.round_number.desc()).first()
    if not last_round:
        return redirect(url_for('index'))
    
    # Delete scores for this round
    Score.query.filter_by(round_id=last_round.id).delete()
    
    # Delete the round
    db.session.delete(last_round)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/round/delete/<int:round_id>', methods=['POST'])
def delete_round(round_id):
    """Delete a specific round and recalculate all subsequent scores."""
    round_obj = Round.query.get(round_id)
    if not round_obj:
        return redirect(url_for('index'))
    
    active_game = Game.query.filter_by(is_active=True).first()
    if not active_game or round_obj.game_id != active_game.id:
        return redirect(url_for('index'))
    
    deleted_round_number = round_obj.round_number
    
    # Delete scores for this round
    Score.query.filter_by(round_id=round_obj.id).delete()
    
    # Delete the round
    db.session.delete(round_obj)
    db.session.commit()
    
    # Renumber subsequent rounds
    subsequent_rounds = Round.query.filter(
        Round.game_id == active_game.id,
        Round.round_number > deleted_round_number
    ).order_by(Round.round_number).all()
    
    for r in subsequent_rounds:
        r.round_number -= 1
    
    db.session.commit()
    
    # Recalculate scores from the deleted round onwards
    recalculate_scores_from_round(active_game.id, deleted_round_number)
    
    return redirect(url_for('index'))

@app.route('/round/edit/<int:round_id>', methods=['GET'])
def edit_round(round_id):
    """Display edit form for a specific round."""
    round_obj = Round.query.get(round_id)
    if not round_obj:
        return redirect(url_for('index'))
    
    active_game = Game.query.filter_by(is_active=True).first()
    if not active_game or round_obj.game_id != active_game.id:
        return redirect(url_for('index'))
    
    players = sorted(active_game.players, key=lambda p: p.id)
    
    # Return JSON for AJAX or render template
    return jsonify({
        'id': round_obj.id,
        'round_number': round_obj.round_number,
        'contract': round_obj.contract_type,
        'main_player_id': round_obj.main_player_id,
        'partner_id': round_obj.partner_id,
        'result': round_obj.result,
        'trump_suit': round_obj.trump_suit,
        'tricks': round_obj.tricks
    })

@app.route('/round/update/<int:round_id>', methods=['POST'])
def update_round(round_id):
    """Update an existing round and recalculate scores."""
    round_obj = Round.query.get(round_id)
    if not round_obj:
        return redirect(url_for('index'))
    
    active_game = Game.query.filter_by(is_active=True).first()
    if not active_game or round_obj.game_id != active_game.id:
        return redirect(url_for('index'))
    
    # Update round data
    round_obj.contract_type = request.form.get('contract')
    round_obj.main_player_id = request.form.get('main_player')
    round_obj.partner_id = request.form.get('partner_id') if request.form.get('partner_id') else None
    round_obj.result = request.form.get('result')
    round_obj.tricks = int(request.form.get('tricks', 0))
    round_obj.trump_suit = request.form.get('trump_suit') if round_obj.contract_type in ['Vraag', 'Abondance', 'Troel', 'Solo'] else None
    
    db.session.commit()
    
    # Recalculate scores from this round onwards
    recalculate_scores_from_round(active_game.id, round_obj.round_number)
    
    return redirect(url_for('index'))

@app.route('/game/end', methods=['POST'])
def end_game():
    active_game = Game.query.filter_by(is_active=True).first()
    if active_game:
        active_game.is_active = False
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/config')
def config():
    """Display configuration page for contract points - only accessible before game starts."""
    active_game = Game.query.filter_by(is_active=True).first()
    
    # Config is only accessible when there's NO active game
    if active_game:
        return redirect(url_for('index'))
    
    # Get the most recent game to use its config, or create a new default config
    latest_game = Game.query.order_by(Game.id.desc()).first()
    
    if latest_game and latest_game.config:
        game_config = latest_game.config
    else:
        # Create a temporary config object with defaults for display
        class TempConfig:
            vraag_partner_points = 2
            vraag_solo_points = 2
            troel_points = 2
            abondance_points = 5
            solo_points = 13
            miserie_points = 10
            grote_miserie_points = 20
            vraag_partner_tricks_won_max = 5
            vraag_partner_tricks_lost_max = 8
            vraag_solo_tricks_won_max = 5
            vraag_solo_tricks_lost_max = 8
            troel_tricks_won_max = 5
            troel_tricks_lost_max = 8
            abondance_tricks_won_max = 4
            abondance_tricks_lost_max = 9
        game_config = TempConfig()
    
    return render_template('config.html', config=game_config, game=None)

@app.route('/config/update', methods=['POST'])
def update_config():
    """Update contract configuration - saves to session for next game."""
    active_game = Game.query.filter_by(is_active=True).first()
    
    # Prevent config changes during active game
    if active_game:
        return "Error: Configuratie kan niet gewijzigd worden tijdens een actief spel.", 403
    
    # Store config values in session to apply to next game
    try:
        from flask import session
        session['pending_config'] = {
            'vraag_partner_points': int(request.form.get('vraag_partner_points', 2)),
            'vraag_solo_points': int(request.form.get('vraag_solo_points', 2)),
            'troel_points': int(request.form.get('troel_points', 2)),
            'abondance_points': int(request.form.get('abondance_points', 5)),
            'solo_points': int(request.form.get('solo_points', 13)),
            'miserie_points': int(request.form.get('miserie_points', 10)),
            'grote_miserie_points': int(request.form.get('grote_miserie_points', 20)),
            'vraag_partner_tricks_won_max': int(request.form.get('vraag_partner_tricks_won_max', 5)),
            'vraag_partner_tricks_lost_max': int(request.form.get('vraag_partner_tricks_lost_max', 8)),
            'vraag_solo_tricks_won_max': int(request.form.get('vraag_solo_tricks_won_max', 5)),
            'vraag_solo_tricks_lost_max': int(request.form.get('vraag_solo_tricks_lost_max', 8)),
            'troel_tricks_won_max': int(request.form.get('troel_tricks_won_max', 5)),
            'troel_tricks_lost_max': int(request.form.get('troel_tricks_lost_max', 8)),
            'abondance_tricks_won_max': int(request.form.get('abondance_tricks_won_max', 4)),
            'abondance_tricks_lost_max': int(request.form.get('abondance_tricks_lost_max', 9))
        }
        
        # Validate all values are positive
        for key, value in session['pending_config'].items():
            if value < 0:
                return "Error: Alle waarden moeten positief zijn.", 400
        
        return redirect(url_for('index'))
    except ValueError:
        return "Error: Ongeldige invoer. Gebruik alleen gehele getallen.", 400

@app.route('/config/reset', methods=['POST'])
def reset_config():
    """Reset configuration to default values."""
    active_game = Game.query.filter_by(is_active=True).first()
    
    # Prevent config changes during active game
    if active_game:
        return "Error: Configuratie kan niet gewijzigd worden tijdens een actief spel.", 403
    
    # Clear pending config from session
    from flask import session
    session.pop('pending_config', None)
    
    return redirect(url_for('config'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
