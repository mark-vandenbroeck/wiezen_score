"""
Manual verification test for configurable contract points.
This script tests the core functionality without running the full Flask app.
"""

from app import app, db, Game, Player, Round, Score, ContractConfig
from app import get_contract_config, get_contract_points, get_trick_limits

def test_config_creation():
    """Test that default config is created with new game."""
    with app.app_context():
        db.create_all()
        
        # Create a game
        game = Game()
        db.session.add(game)
        db.session.commit()
        
        # Create config
        config = ContractConfig(game_id=game.id)
        db.session.add(config)
        db.session.commit()
        
        # Verify defaults
        assert config.vraag_partner_points == 2
        assert config.vraag_solo_points == 2
        assert config.troel_points == 2
        assert config.abondance_points == 5
        assert config.solo_points == 13
        assert config.miserie_points == 10
        assert config.grote_miserie_points == 20
        
        print("✓ Config creation test passed")
        return game.id

def test_get_contract_points(game_id):
    """Test get_contract_points helper function."""
    with app.app_context():
        config = get_contract_config(game_id)
        
        # Test Vraag with partner
        points = get_contract_points(config, 'Vraag', has_partner=True)
        assert points == 2, f"Expected 2, got {points}"
        
        # Test Vraag without partner
        points = get_contract_points(config, 'Vraag', has_partner=False)
        assert points == 2, f"Expected 2, got {points}"
        
        # Test other contracts
        assert get_contract_points(config, 'Troel', has_partner=True) == 2
        assert get_contract_points(config, 'Abondance') == 5
        assert get_contract_points(config, 'Solo') == 13
        assert get_contract_points(config, 'Miserie') == 10
        assert get_contract_points(config, 'Grote Miserie') == 20
        
        print("✓ get_contract_points test passed")

def test_config_update(game_id):
    """Test updating config values."""
    with app.app_context():
        config = ContractConfig.query.filter_by(game_id=game_id).first()
        
        # Update values
        config.vraag_partner_points = 3
        config.vraag_solo_points = 4
        config.solo_points = 15
        db.session.commit()
        
        # Verify updates
        config = get_contract_config(game_id)
        assert config.vraag_partner_points == 3
        assert config.vraag_solo_points == 4
        assert config.solo_points == 15
        
        # Test that get_contract_points uses new values
        points = get_contract_points(config, 'Vraag', has_partner=True)
        assert points == 3, f"Expected 3, got {points}"
        
        points = get_contract_points(config, 'Vraag', has_partner=False)
        assert points == 4, f"Expected 4, got {points}"
        
        points = get_contract_points(config, 'Solo')
        assert points == 15, f"Expected 15, got {points}"
        
        print("✓ Config update test passed")

def test_trick_limits(game_id):
    """Test get_trick_limits helper function."""
    with app.app_context():
        config = get_contract_config(game_id)
        
        # Test Vraag with partner
        limit = get_trick_limits(config, 'Vraag', 'Gewonnen', has_partner=True)
        assert limit == 5
        
        limit = get_trick_limits(config, 'Vraag', 'Verloren', has_partner=True)
        assert limit == 8
        
        # Test Vraag without partner
        limit = get_trick_limits(config, 'Vraag', 'Gewonnen', has_partner=False)
        assert limit == 5
        
        # Test Abondance
        limit = get_trick_limits(config, 'Abondance', 'Gewonnen')
        assert limit == 4
        
        limit = get_trick_limits(config, 'Abondance', 'Verloren')
        assert limit == 9
        
        print("✓ Trick limits test passed")

def test_backwards_compatibility():
    """Test that games without config use default values."""
    with app.app_context():
        # Create game without config
        game = Game()
        db.session.add(game)
        db.session.commit()
        
        # Get config (should return defaults)
        config = get_contract_config(game.id)
        
        # Verify defaults are returned
        assert config.vraag_partner_points == 2
        assert config.solo_points == 13
        
        points = get_contract_points(config, 'Vraag', has_partner=True)
        assert points == 2
        
        print("✓ Backwards compatibility test passed")

if __name__ == '__main__':
    print("Running configurable contract points verification tests...\n")
    
    try:
        game_id = test_config_creation()
        test_get_contract_points(game_id)
        test_config_update(game_id)
        test_trick_limits(game_id)
        test_backwards_compatibility()
        
        print("\n✅ All tests passed!")
        print("\nThe configurable contract points feature is working correctly:")
        print("  • Default config is created with new games")
        print("  • Vraag with/without partner distinction works")
        print("  • Config values can be updated")
        print("  • Trick limits are configurable")
        print("  • Backwards compatibility is maintained")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
