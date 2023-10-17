#!/usr/bin/python3

from datetime import datetime, timedelta
from bot import bot_take_mulligan, find_bot_move, get_bot_deck
from card import Card
from card_templates_list import CARD_TEMPLATES
from common_decks import create_common_decks
from database import SessionLocal
from db_card import DbCard
from db_deck import DbDeck, add_db_deck
from db_game import DbGame
from deck import Deck
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_cors import CORS
from game import Game
import traceback
from functools import wraps
import random
from _thread import start_new_thread
from lane_rewards import LANE_REWARDS

from redis_utils import rdel, rget_json, rlock, rset_json
from settings import COMMON_DECK_USERNAME, LOCAL
from utils import generate_unique_id, get_game_lock_redis_key, get_game_redis_key, get_game_with_hidden_information_redis_key, get_staged_game_lock_redis_key, get_staged_game_redis_key, get_staged_moves_redis_key


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)


def bot_move_in_game(game: Game, player_num: int) -> None:
    assert game.game_state 
    bot_move = find_bot_move(player_num, game.game_state)
    print('The bot has chosen the following move: ', bot_move)
    game_id = game.id
    with rlock(get_game_lock_redis_key(game_id)):
        game_json = rget_json(get_game_redis_key(game_id))    
        if not game_json:
            return
        game_from_json = Game.from_json(game_json)

        # Should be redundant, but I think there's some issue on the first turn where this sometimes isn't true
        game_from_json.is_bot_by_player[player_num] = True 

        assert game_from_json.game_state

        # if not game.game_state.has_moved_by_player[1 - player_num]:
        #     rset_json(get_game_with_hidden_information_redis_key(game.id), {1 - player_num: game.to_json()}, ex=24 * 60 * 60)

        # try:
        #     for card_id, lane_number in bot_move.items():
        #         staged_game_from_json.game_state.play_card(player_num, card_id, lane_number)
        # except Exception:
        #     print(f'The bot tried to play an invalid move: {bot_move}.')
        #     hidden_info_game = rget_json(get_game_with_hidden_information_redis_key(game.id))
        #     if hidden_info_game is not None and hidden_info_game.get(player_num) is not None:
        #         game_from_hidden_json = Game.from_json(hidden_info_game[player_num])
        #         assert game_from_hidden_json.game_state
        #         bot_move = find_bot_move(player_num, game_from_hidden_json.game_state)
        #     else:
        #         game_from_nonhidden_json = Game.from_json(game_json)
        #         assert game_from_nonhidden_json.game_state
        #         bot_move = find_bot_move(player_num, game_from_nonhidden_json.game_state)

        #     try:
        #         for card_id, lane_number in bot_move.items():
        #             game_from_json.game_state.play_card(player_num, card_id, lane_number)
        #     except Exception:
        #         print(f'The bot tried to play an invalid move: {bot_move} again. Giving up.')

        game_from_json.game_state.has_moved_by_player[player_num] = True        

        have_moved = game_from_json.game_state.all_players_have_moved()
        if have_moved:
            for card_id, lane_number in bot_move.items():
                try:
                    game_from_json.game_state.play_card(player_num, card_id, lane_number)
                except Exception:
                    print(f'The bot tried to play an invalid move: {bot_move}.')
                    continue

            staged_moves_for_other_player = rget_json(get_staged_moves_redis_key(game_id, 1 - player_num)) or {}
            for card_id, lane_number in staged_moves_for_other_player.items():
                try:
                    game_from_json.game_state.play_card(1 - player_num, card_id, lane_number)
                except Exception:
                    print(f'The player tried to play an invalid move: {bot_move}.')
                    continue

            game_from_json.game_state.roll_turn()
            rdel(get_game_with_hidden_information_redis_key(game.id))
            rset_json(get_staged_moves_redis_key(game_id, 0), {}, ex=24 * 60 * 60)
            rset_json(get_staged_moves_redis_key(game_id, 1), {}, ex=24 * 60 * 60)
            rdel(get_staged_game_redis_key(game_id, 0))
            rdel(get_staged_game_redis_key(game_id, 1))

        else:
            rset_json(get_staged_moves_redis_key(game_id, player_num), bot_move, ex=24 * 60 * 60)

        rset_json(get_game_redis_key(game_id), game_from_json.to_json(), ex=24 * 60 * 60)

        if have_moved:
            socketio.emit('update', room=game_id)



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
    @wraps(func)
    def wrapper(*args, **kwargs):
        try: 
            with SessionLocal() as sess:
                kwargs['sess'] = sess
                try:
                    response = func(*args, **kwargs)
                except Exception as e:
                    sess.rollback()
                    raise e
                finally:
                    sess.close()
            return recurse_to_json(response)
        except Exception as e:
            print(traceback.print_exc())
            return jsonify({"error": "Unexpected error"}), 500

    return wrapper


@app.route('/api/card_pool', methods=['GET'])
@api_endpoint
def get_card_pool(sess):
    print('Getting card pool')
    return recurse_to_json({'cards': CARD_TEMPLATES, 'laneRewards': LANE_REWARDS})


@app.route('/api/decks', methods=['POST'])
@api_endpoint
def create_deck(sess):
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    cards = data.get('cards')
    if cards is None:
        return jsonify({"error": "Cards data is required"}), 400

    username = data.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400

    deck_name = data.get('name')
    if not deck_name:
        return jsonify({"error": "Deck name is required"}), 400

    lane_reward_name = data.get('laneRewardName') or None

    # Process the cards data as needed, e.g., save to a database or check game state
    
    deck_with_same_name = (
        sess.query(DbDeck)
        .filter(DbDeck.username == username)
        .filter(DbDeck.name == deck_name)
        .first()
    )

    if deck_with_same_name:
        for card in deck_with_same_name.cards:
            sess.delete(card)
        sess.commit()
        sess.delete(deck_with_same_name)
        sess.commit()
    
    db_deck = add_db_deck(sess, cards, username, deck_name, lane_reward_name)

    return jsonify(Deck.from_db_deck(db_deck).to_json())


@app.route('/api/decks', methods=['DELETE'])
@api_endpoint
def delete_deck(sess):
    deck_name = request.args.get('deckName')
    username = request.args.get('username')
    deck_id = request.args.get('deckId')

    if not (deck_name or deck_id):
        return jsonify({"error": "Deck name or ID is required"}), 400
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    if deck_id:
        db_deck = sess.query(DbDeck).get(deck_id)
        if not db_deck:
            return jsonify({"error": "Deck not found"}), 404
    
    else:
        assert deck_name
        db_deck = sess.query(DbDeck).filter(DbDeck.username == username).filter(DbDeck.name == deck_name).first()
        if not db_deck:
            return jsonify({"error": "Deck not found"}), 404

    for card in db_deck.cards:
        sess.delete(card)
    sess.commit()
    sess.delete(db_deck)
    sess.commit()

    return jsonify({"success": True})


@app.route('/api/decks/rename', methods=['POST'])
@api_endpoint
def rename_deck(sess):
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    deck_id = data.get('deckId')
    deck_name = data.get('deckName')
    username = data.get('username')
    new_deck_name = data.get('newDeckName')
    if not (deck_id or deck_name):
        return jsonify({"error": "Deck ID or deck name is required"}), 400
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    if deck_id:
        db_deck = sess.query(DbDeck).get(deck_id)
        if not db_deck:
            return jsonify({"error": "Deck not found"}), 404
        
    else:
        assert deck_name
        db_deck = sess.query(DbDeck).filter(DbDeck.username == username).filter(DbDeck.name == deck_name).first()
        if not db_deck:
            return jsonify({"error": "Deck not found"}), 404

    db_deck.name = new_deck_name
    sess.commit()

    return jsonify({"success": True})


@app.route('/api/decks', methods=['GET'])
@api_endpoint
def get_decks(sess):
    username = request.args.get('username')
    common_decks = (
        sess.query(DbDeck)
        .filter(DbDeck.username == COMMON_DECK_USERNAME)
        .order_by(DbDeck.name)
        .all()
    )

    user_decks = (
        sess.query(DbDeck)
        .filter(DbDeck.username == username)
        .order_by(DbDeck.name)
        .all()
    )

    db_decks = [*common_decks, *user_decks]

    decks = [Deck.from_db_deck(db_deck) for db_deck in db_decks]
    return recurse_to_json([deck for deck in decks if deck.username in [request.args.get('username'), COMMON_DECK_USERNAME]])


@app.route('/api/host_game', methods=['POST'])
@api_endpoint
def host_game(sess):
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    deck_id = data.get('deckId')
    deck_name = data.get('deckName')

    if not (deck_id or deck_name):
        return jsonify({"error": "Deck ID or name is required"}), 400
    
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    host_game_id = data.get('hostGameId')

    is_bot_game = bool(data.get('bot_game'))
    
    if deck_id:
        db_deck = sess.query(DbDeck).get(deck_id)
        if not db_deck:
            return jsonify({"error": "Deck not found"}), 404
        deck = Deck.from_db_deck(db_deck)
    else:
        assert deck_name
        db_deck = sess.query(DbDeck).filter(DbDeck.username.in_([username, COMMON_DECK_USERNAME])).filter(DbDeck.name == deck_name).first()
        if not db_deck:
            return jsonify({"error": "Deck not found"}), 404
        deck = Deck.from_db_deck(db_deck)

    if is_bot_game:
        player_0_username = username
        player_1_username = 'RUFUS_THE_ROBOT'

        bot_deck = get_bot_deck(sess, deck.name) or deck
        game = Game({0: username, 1: 'RUFUS_THE_ROBOT'}, {0: deck, 1: bot_deck}, id=host_game_id)
        game.is_bot_by_player[1] = True
        game.start()
        
        player_0_deck = deck
        player_1_deck = bot_deck

        socketio.emit('update', room=game.id)      

        assert game.game_state
        bot_take_mulligan(game.game_state, 1)

        start_new_thread(bot_move_in_game, (game, 1))

    else:
        player_0_username = username
        player_1_username = None
        player_0_deck = deck
        player_1_deck = None

    game = Game({0: player_0_username, 1: player_1_username}, {0: player_0_deck, 1: player_1_deck}, id=host_game_id)
    sess.add(DbGame(
        id=game.id,
        player_0_username=player_0_username,
        player_1_username=player_1_username,
    ))
    sess.commit()

    with rlock(get_game_lock_redis_key(game.id)):
        rset_json(get_game_redis_key(game.id), game.to_json(), ex=24 * 60 * 60)

    return jsonify({"gameId": game.id})


@app.route('/api/join_game', methods=['POST'])
@api_endpoint
def join_game(sess):
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
    deck_name = data.get('deckName')

    if not (deck_id or deck_name):
        return jsonify({"error": "Deck ID or name is required"}), 400

    with rlock(get_game_lock_redis_key(game_id)):
        game_json = rget_json(get_game_redis_key(game_id))
        if not game_json:
            return jsonify({"error": "Game not found"}), 404
        
        game = Game.from_json(game_json)

        if deck_id:
            db_deck = sess.query(DbDeck).get(deck_id)
            if not db_deck:
                return jsonify({"error": "Deck not found"}), 404
            deck = Deck.from_db_deck(db_deck)
        else:
            assert deck_name
            db_deck = sess.query(DbDeck).filter(DbDeck.username.in_([username, COMMON_DECK_USERNAME])).filter(DbDeck.name == deck_name).first()
            if not db_deck:
                return jsonify({"error": "Deck not found"}), 404
            deck = Deck.from_db_deck(db_deck)

        game.usernames_by_player[1] = username
        game.decks_by_player[1] = deck
        game.start()
        
        rset_json(get_game_redis_key(game.id), game.to_json(), ex=24 * 60 * 60)

        socketio.emit('update', room=game.id)

    db_game = sess.query(DbGame).get(game.id)
    db_game.player_1_username = username

    sess.commit()
    
    return jsonify({"gameId": game.id})


@app.route('/api/open_games', methods = ['GET'])
@api_endpoint
def get_available_games(sess):
    game_ids_with_no_player_1 = (
        sess.query(DbGame)
        .filter(DbGame.player_1_username.is_(None))
        .filter(DbGame.created_at > datetime.now() - timedelta(hours=2))
        .all()
    )

    return recurse_to_json({'games': game_ids_with_no_player_1})


@app.route('/api/games/<game_id>', methods=['GET'])
@api_endpoint
def get_game(sess, game_id):
    player_num = int(raw_player_num) if (raw_player_num := request.args.get('playerNum')) is not None else None

    staged_game_json = rget_json(get_staged_game_redis_key(game_id, player_num))

    if staged_game_json:
        return recurse_to_json(staged_game_json)
    
    else:
        game_json = rget_json(get_game_redis_key(game_id))

        if not game_json:
            return jsonify({"error": "Game not found"}), 404   

        return recurse_to_json(game_json)


@app.route('/api/games/<game_id>/take_turn', methods=['POST'])
@api_endpoint
def take_turn(sess, game_id):
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    cards_to_lanes = data.get('cardsToLanes')

    if cards_to_lanes is None:
        return jsonify({"error": "Cards mapping is required"}), 400
    
    with rlock(get_game_lock_redis_key(game_id)):
        game_json = rget_json(get_game_redis_key(game_id))
        if not game_json:
            return jsonify({"error": "Game not found"}), 404

        game = Game.from_json(game_json)

        player_num = game.username_to_player_num(username)
        assert player_num is not None
        assert game.game_state is not None

        if not game.game_state.has_moved_by_player[1 - player_num]:
            rset_json(get_game_with_hidden_information_redis_key(game.id), {1 - player_num: game.to_json()}, ex=24 * 60 * 60)

        for card_id, lane_number in cards_to_lanes.items():
            game.game_state.play_card(player_num, card_id, lane_number)

        game.game_state.has_moved_by_player[player_num] = True
        have_moved = game.game_state.all_players_have_moved()
        if have_moved:
            game.game_state.roll_turn()
            rdel(get_game_with_hidden_information_redis_key(game.id))
            rset_json(get_staged_moves_redis_key(game_id, 0), {}, ex=24 * 60 * 60)
            rset_json(get_staged_moves_redis_key(game_id, 1), {}, ex=24 * 60 * 60)
            rdel(get_staged_game_redis_key(game_id, 0))
            rdel(get_staged_game_redis_key(game_id, 1))


        if game.is_bot_by_player[1 - player_num] and not game.game_state.has_moved_by_player[1 - player_num]:
            start_new_thread(bot_move_in_game, (game, 1 - player_num))

        rset_json(get_game_redis_key(game.id), game.to_json(), ex=24 * 60 * 60)
    
    if have_moved:
        socketio.emit('update', room=game.id)

    return jsonify({"gameId": game.id,
                    "game": game.to_json()})


@app.route('/api/games/<game_id>/play_card', methods=['POST'])
@api_endpoint
def play_card(sess, game_id):
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400

    card_id = data.get('cardId')

    if card_id is None:
        return jsonify({"error": "Card ID is required"}), 400
    
    lane_number = data.get('laneNumber')

    if lane_number is None:
        return jsonify({"error": "Lane number is required"}), 400
    
    player_num = data.get('playerNum')

    if player_num is None:
        return jsonify({"error": "Player number is required"}), 400

    with rlock(get_staged_game_lock_redis_key(game_id, player_num)):
        game_json = rget_json(get_staged_game_redis_key(game_id, player_num))
        if not game_json:
            game_json = rget_json(get_game_redis_key(game_id))

        staged_moves = rget_json(get_staged_moves_redis_key(game_id, player_num)) or {}

        game = Game.from_json(game_json)

        assert player_num is not None
        assert game.game_state is not None

        print([card.id for card in game.game_state.hands_by_player[player_num]])

        game.game_state.play_card(player_num, card_id, lane_number)
        staged_moves[card_id] = lane_number

        rset_json(get_staged_moves_redis_key(game_id, player_num), staged_moves, ex=24 * 60 * 60)
        rset_json(get_staged_game_redis_key(game_id, player_num), game.to_json(), ex=24 * 60 * 60)

    return jsonify({"gameId": game.id,
                    "game": game.to_json()})


@app.route('/api/games/<game_id>/submit_turn', methods=['POST'])
@api_endpoint
def submit_turn(sess, game_id):
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400

    player_num = data.get('playerNum')

    if player_num is None:
        return jsonify({"error": "Player number is required"}), 400

    with rlock(get_game_lock_redis_key(game_id)):
        game_json = rget_json(get_game_redis_key(game_id))
        if not game_json:
            return jsonify({"error": "Game not found"}), 404

        game = Game.from_json(game_json)

        assert player_num is not None
        assert game.game_state is not None

        game.game_state.has_moved_by_player[player_num] = True
        have_moved = game.game_state.all_players_have_moved()
        if have_moved:
            for player_num_to_make_moves_for in [0, 1]:
                staged_moves = rget_json(get_staged_moves_redis_key(game_id, player_num_to_make_moves_for)) or {}

                print('Making moves for player ', player_num_to_make_moves_for)
                print(staged_moves)

                for card_id, lane_number in staged_moves.items():
                    try:
                        game.game_state.play_card(player_num_to_make_moves_for, card_id, lane_number)
                    except Exception:
                        print(f'Player {player_num_to_make_moves_for} tried to play an invalid move: {card_id} -> {lane_number}.')
                        continue

            game.game_state.roll_turn()
            rdel(get_game_with_hidden_information_redis_key(game.id))
            rset_json(get_staged_moves_redis_key(game_id, 0), {}, ex=24 * 60 * 60)
            rset_json(get_staged_moves_redis_key(game_id, 1), {}, ex=24 * 60 * 60)
            rdel(get_staged_game_redis_key(game_id, 0))
            rdel(get_staged_game_redis_key(game_id, 1))

        if game.is_bot_by_player[1 - player_num] and not game.game_state.has_moved_by_player[1 - player_num]:
            start_new_thread(bot_move_in_game, (game, 1 - player_num))

        rset_json(get_game_redis_key(game.id), game.to_json(), ex=24 * 60 * 60)
    
    if have_moved:
        socketio.emit('update', room=game.id)

    return jsonify({"gameId": game.id,
                    "game": game.to_json()})


@app.route('/api/games/<game_id>/unsubmit_turn', methods=['POST'])
@api_endpoint
def unsubmit_turn(sess, game_id):
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    player_num = data.get('playerNum')

    if player_num is None:
        return jsonify({"error": "Player number is required"}), 400

    with rlock(get_game_lock_redis_key(game_id)):
        game_json = rget_json(get_game_redis_key(game_id))
        if not game_json:
            return jsonify({"error": "Game not found"}), 404

        game = Game.from_json(game_json)

        player_num = game.username_to_player_num(username)
        assert player_num is not None
        assert game.game_state is not None

        game.game_state.has_moved_by_player[player_num] = False

        rset_json(get_game_redis_key(game.id), game.to_json(), ex=24 * 60 * 60)

    return jsonify({"gameId": game.id,
                    "game": game.to_json()})


@app.route('/api/games/<game_id>/reset_turn', methods=['POST'])
@api_endpoint
def reset_turn(sess, game_id):
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400

    player_num = data.get('playerNum')

    if player_num is None:
        return jsonify({"error": "Player number is required"}), 400

    with rlock(get_staged_game_lock_redis_key(game_id, player_num)):
        rdel(get_staged_game_redis_key(game_id, player_num))
        rdel(get_staged_moves_redis_key(game_id, player_num))

    return jsonify({"gameId": game_id})


@app.route('/api/games/<game_id>/mulligan', methods=['POST'])
@api_endpoint
def mulligan(sess, game_id):
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    cards_to_mulligan = data.get('cards')

    if cards_to_mulligan is None:
        return jsonify({"error": "Cards mapping is required"}), 400
    
    with rlock(get_game_lock_redis_key(game_id)):
        game_json = rget_json(get_game_redis_key(game_id))
        if not game_json:
            return jsonify({"error": "Game not found"}), 404

        game = Game.from_json(game_json)

        player_num = game.username_to_player_num(username)
        assert player_num is not None
        assert game.game_state is not None

        random.shuffle(cards_to_mulligan)

        for card_id in cards_to_mulligan:
            game.game_state.mulligan_card(player_num, card_id)

        game.game_state.has_mulliganed_by_player[player_num] = True

        rset_json(get_game_redis_key(game.id), game.to_json(), ex=24 * 60 * 60)

    return jsonify({"gameId": game.id,
                    "game": game.to_json()})


@app.route('/api/games/<game_id>/mulligan_all', methods=['POST'])
@api_endpoint
def mulligan_all(sess, game_id):
    data = request.json

    if not data:
        return jsonify({"error": "Invalid data"}), 400
    
    username = data.get('username')

    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    mulliganing = data.get('mulliganing')

    with rlock(get_game_lock_redis_key(game_id)):
        game_json = rget_json(get_game_redis_key(game_id))
        if not game_json:
            return jsonify({"error": "Game not found"}), 404

        game = Game.from_json(game_json)

        player_num = game.username_to_player_num(username)
        assert player_num is not None
        assert game.game_state is not None

        if mulliganing:
            game.game_state.mulligan_all(player_num)

        game.game_state.has_mulliganed_by_player[player_num] = True

        rset_json(get_game_redis_key(game.id), game.to_json(), ex=24 * 60 * 60)
    
    # Silly kludge to prevent leakage of hidden info because I didn't want to bother using the hidden_game_info logic
    for lane in game.game_state.lanes:
        lane.characters_by_player[0] = [character for character in lane.characters_by_player[0] if not character.template.name == 'Elephant Rat']
        lane.characters_by_player[1] = [character for character in lane.characters_by_player[1] if not character.template.name == 'Elephant Rat']

    return jsonify({"gameId": game.id,
                    "game": game.to_json()})

@socketio.on('connect')
def on_connect():
    print('Connected')

@socketio.on('join')
def on_join(data):
    username = data['username'] if 'username' in data else 'anonymous'
    room = data['room']
    join_room(room)
    print(f'{username} joined {room}')
    
@socketio.on('leave')
def on_leave(data):
    username = data['username'] if 'username' in data else 'anonymous'
    room = data['room']
    leave_room(room)
    print(f'{username} left {room}') 

if __name__ == '__main__':
    create_common_decks()

    if LOCAL:
        socketio.run(app, host='0.0.0.0', port=5001, debug=True)
    else:
        socketio.run(app, host='0.0.0.0', port=5007)
