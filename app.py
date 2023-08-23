from datetime import datetime, timedelta
from card_templates_list import CARD_TEMPLATES
from deck import Deck
from flask import Flask, jsonify, request
from flask_cors import CORS
from game import Game

from redis_utils import rget_json, rlock, rset_json
from utils import generate_unique_id


app = Flask(__name__)
CORS(app)


def recurse_to_json(obj):
    if isinstance(obj, dict):
        return {k: recurse_to_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [recurse_to_json(v) for v in obj]
    elif hasattr(obj, 'to_json'):
        return obj.to_json()
    else:
        return obj


# decorator that takes in an api endpoint and calls recurse_to_json on its result
def api_endpoint(func):
    def wrapper(*args, **kwargs):
        return jsonify(recurse_to_json(func(*args, **kwargs)))
    return wrapper


@app.route('/api/card_pool', methods=['GET'])
def get_card_pool():
    return recurse_to_json(CARD_TEMPLATES)


@app.route('/api/decks', methods=['POST'])
def create_deck():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    cards = data.get('cards')
    if not cards:
        return jsonify({"error": "Cards data is required"}), 400

    username = data.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400

    deck_name = data.get('name')
    if not deck_name:
        return jsonify({"error": "Deck name is required"}), 400

    # Process the cards data as needed, e.g., save to a database or check game state
    with rlock('decks'):
        decks = rget_json('decks') or {}
        deck = Deck(cards, username, deck_name)
        deck_id = deck.id
        decks[deck_id] = deck.to_json()
        rset_json('decks', decks)

    return jsonify(deck.to_json())


@app.route('/api/decks', methods=['GET'])
def get_decks():
    decks_json = rget_json('decks') or {}
    decks = [Deck.from_json(deck_json) for deck_json in decks_json.values()]
    return recurse_to_json([deck for deck in decks if deck.username == request.args.get('username')])


@app.route('/api/host_game', methods=['POST'])
def host_game():
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    deck_id = data.get('deckId')

    if not deck_id:
        return jsonify({"error": "Deck ID is required"}), 400
    
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    with rlock('games'):
        decks = rget_json('decks') or {}
        deck_json = decks.get(deck_id)
        if not deck_json:
            return jsonify({"error": "Deck not found"}), 404
        deck = Deck.from_json(deck_json)

        game = Game({0: username, 1: None}, {0: deck, 1: None})
        games = rget_json('games') or {}
        games[game.id] = game.to_json()

        for game_id in games:
            # Delete games that are more than 1 day old

            if datetime.now() - datetime.fromtimestamp(games[game_id]['created_at']) > timedelta(days=1):
                del games[game.id]

        rset_json('games', games)
    
    return jsonify({"gameId": game.id})


@app.route('/api/games', methods=['GET'])
def get_games():
    games = rget_json('games') or {}
    return jsonify(list(games.values()))


@app.route('/api/join_game', methods=['POST'])
def join_game():
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    game_id = data.get('gameId')

    if not game_id:
        return jsonify({"error": "Game ID is required"}), 400
    
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    deck_id = data.get('deckId')

    if not deck_id:
        return jsonify({"error": "Deck ID is required"}), 400

    with rlock('games'):
        games = rget_json('games') or {}
        game_json = games.get(game_id)
        if not game_json:
            return jsonify({"error": "Game not found"}), 404
        
        game = Game.from_json(game_json)

        decks = rget_json('decks') or {}
        deck_json = decks.get(deck_id)
        if not deck_json:
            return jsonify({"error": "Deck not found"}), 404
        deck = Deck.from_json(deck_json)

        game.usernames_by_player[1] = username
        game.decks_by_player[1] = deck
        game.start()
        rset_json('games', games)
    
    return jsonify({"gameId": game.id})


@app.route('/api/games/<game_id>', methods=['GET'])
def get_game(game_id):
    games = rget_json('games') or {}
    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    return recurse_to_json(game)


@app.route('/api/games/<game_id>/take_turn', methods=['POST'])
def take_turn(game_id):
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    cards_to_lanes = data.get('cardsToLanes')

    if not cards_to_lanes:
        return jsonify({"error": "Cards mapping is required"}), 400
    
    with rlock('games'):
        games = rget_json('games') or {}
        game_json = games.get(game_id)
        if not game_json:
            return jsonify({"error": "Game not found"}), 404

        game = Game.from_json(game_json)

        player_num = game.username_to_player_num(username)
        assert player_num is not None
        assert game.game_state is not None

        for card_id, lane_number in cards_to_lanes.items():
            game.game_state.play_card(player_num, card_id, lane_number)

        game.game_state.has_moved_by_player[player_num] = True
        if game.game_state.all_players_have_moved():
            game.game_state.roll_turn()

        games[game_id] = game.to_json()

        rset_json('games', games)
    
    return jsonify({"gameId": game.id})



if __name__ == '__main__':
    app.run(debug=True)