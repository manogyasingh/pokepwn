from include import Ply, RPly, CHARIZARD, BLASTOISE, VENUSAUR, PIKACHU, Battle, BattleOrder, TEAMS, valid_move, get_pokemon, calc_damage
from poke_env.environment.move import Move
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.status import Status
import numpy as np
import random 
import math
"""
Use Ply.possible_moves(battle) to get a list of all possible actions that you can take.
Function valid_move(battle, move) returns True if the chosen move passes basic sanity checks for the current battle.
Still, try to make sure your chosen move is in the possible moves returned by Ply.possible_moves.
order = Pokemon to switch, or move to use
"""
"""
Use battle.active_pokemon to get the Pokemon object for your current active pokemon
Use battle.opponent_active_pokemon to get the Pokemon object for the opponent's current active pokemon
Use battle.team or battle.opponent_team to get a dict of <identifier, Pokemon object> for either side's team
"""
"""
Use pokemon.current_hp_fraction to get the hp % of a pokemon.
Use pokemon.types to get the list of types for a pokemon 
Use get_pokemon(pokemon) on the pokemon object, to get the moves and stats for the opponent pokemon
These can be accessed using pokemon.moves (which returns a dict of <identifier, Move object>)
and pokemon.stats (which returns a dict of <stat, stat value>)
You can use math.floor(pokemon.stats["hp"] * pokemon.current_hp_fraction) to find the absolute
value of hp remaining.
Use calc_damage(pkmn1, pkmn2) to get a dict of <move, damage_values> for each move of pkmn1 against pkmn2.
damage_values is a list of 16 integers, each of which is equally likely to be the amount of damage dealt.
There is a 1/24 chance of a critical hit, and you can do calc_damage(pkmn1, pkmn2, is_crit=True) to find
the damage_values in case of a critical hit.
You can subtract this value from the value of hp remaining, to get the pokemon's new hp after 
the attack. Do NOT edit the pokemon._current_hp field as it is private (maintained by the simulator),
instead just use the method described above to track the hp.
"""
"""
Use pokemon.status_counter to find the turn count for sleep / toxic.
Use pokemon.status to find the status of a Pokemon 
(Status.SLP = sleeping, Status.TOX = toxic poison)
"""
"""
Use move.type to find the type of a move
Use move.type.damage_multiplier(*pokemon.types, type_chart=GenData.from_gen(7).type_chart) to find move effectiveness on pokemon object
Use move.base_power and move.accuracy to find the details of a move.
Use move.recoil to find % of damage dealt by move as recoil.
Use move.current_pp to find the remaining pp for a move.
You can use compare this value to figure out the move of the opponent on the previous turn.
"""
"""
The Ply.possible_moves returns a list of BattleOrder objects.
Each of them are either:
object.order is a Move (indicating an attack)
object.order is a Pokemon (indicating a switch)
"""
"""
The choose_move_strongest(battle) function is given, to give an idea of a basic AI that is (much) better than random.
It picks the move that is strongest against the current opposite Pokemon.
How can you improve it?
It does not use status moves (Sleep Powder, Toxic, Taunt, Recover). 
It does not switch Pokemon or account for enemy switching. 
It does not account for the enemy Pokemon damage dealt to you.
It does not account for the enemy Pokemon being faster than you (and possible KOing you first).
"""

# Sleep > Recover > Toxic > Taunt

def handle_toxic(battle):
    """
    Uses toxic if available and the enemy Pokemon is not resistant or immune to it,
    and the Pokemon doesn't already have poison status.
    Otherwise returns choose_move_strongest().
    
    Args:
        battle: Current battle state
        
    Returns:
        BattleOrder: Toxic move or result of choose_move_strongest()
    """
    all_moves = Ply.possible_moves(battle)
    my_pkmn = battle.active_pokemon
    enem_pkmn = get_pokemon(battle.opponent_active_pokemon)
    
    # Check if enemy already has a status condition
    if enem_pkmn.status is not None:
        return handle_taunt(battle)
    
    # Check if we have toxic
    toxic_move = None
    for move in all_moves:
        if isinstance(move.order, Move) and move.order.id.lower() == "toxic":
            toxic_move = move
            break
    
    # If no toxic move, use strongest move
    if not toxic_move or toxic_move.order.current_pp <= 0:
        return handle_taunt(battle)
    
    # Check if enemy is resistant or immune to poison
    resistant_types = ["poison", "steel", "ground", "rock", "ghost"]
    enemy_types = [t.name.lower() for t in enem_pkmn.types]
    
    # Check if any of the enemy's types are resistant to poison
    is_resistant = any(t in resistant_types for t in enemy_types)
    
    # If enemy is not resistant, use toxic
    if not is_resistant:
        return toxic_move
    
    # Otherwise use strongest move
    return handle_taunt(battle)

def handle_taunt(battle):
    return choose_move_strongest(battle)
    """
    Uses taunt if available and the enemy Pokemon has either toxic or sleep powder.
    Otherwise calls handle_recover().
    
    Args:
        battle: Current battle state
        
    Returns:
        BattleOrder: Taunt move or result of handle_recover()
    """
    all_moves = Ply.possible_moves(battle)
    my_pkmn = battle.active_pokemon
    enem_pkmn = get_pokemon(battle.opponent_active_pokemon)
    
    # Check if enemy has toxic or sleep powder
    enemy_has_status_move = False
    for move_id, move in enem_pkmn.moves.items():
        if ("toxic" in move_id.lower() or 
            "sleep" in move_id.lower() or 
            "spore" in move_id.lower()):
            enemy_has_status_move = True
            break
    
    # Check if we have taunt
    taunt_move = None
    for move in all_moves:
        if isinstance(move.order, Move) and move.order.id.lower() == "taunt":
            taunt_move = move
            break
    
    # If we have taunt, enemy has status moves, and we have PP, use taunt
    if taunt_move and enemy_has_status_move and taunt_move.order.current_pp > 0:
        return taunt_move
    
    return choose_move_strongest(battle)

def handle_recover(battle):
    """
    Uses recover if available and the Pokemon has at most 60% health.
    Otherwise calls handle_sleep().
    
    Args:
        battle: Current battle state
        
    Returns:
        BattleOrder: Recover move or result of handle_sleep()
    """
    all_moves = Ply.possible_moves(battle)
    my_pkmn = battle.active_pokemon
    enem_pkmn = get_pokemon(battle.opponent_active_pokemon)
    
    # Check if we have recover and HP is at most 60%
    recover_move = None
    for move in all_moves:
        if isinstance(move.order, Move) and move.order.id.lower() == "recover":
            recover_move = move
            break
    
    # If we don't have recover move or no PP, use handle_sleep
    if not recover_move or recover_move.order.current_pp <= 0:
        return handle_toxic(battle)
    
    # Calculate current HP and post-recovery HP (recover restores 50% of max HP)
    our_max_hp = my_pkmn.stats["hp"]
    our_current_hp = math.floor(our_max_hp * my_pkmn.current_hp_fraction)
    recover_amount = math.floor(our_max_hp * 0.5)
    post_recovery_hp = min(our_max_hp, our_current_hp + recover_amount)
    post_recovery_fraction = post_recovery_hp / our_max_hp
    
    # Calculate max damage enemy can do
    opp_damages = calc_damage(enem_pkmn, my_pkmn)
    max_opp_damage = 0
    if opp_damages:
        for damage_values in opp_damages.values():
            avg_damage = np.mean(damage_values)
            if avg_damage > max_opp_damage:
                max_opp_damage = avg_damage
    
    # Check speed
    our_speed = my_pkmn.stats.get("spe", 0)
    opp_speed = enem_pkmn.stats.get("spe", 0)
    we_are_slower = our_speed < opp_speed
    
    # If enemy can knock us out after recovery or we're slower and enemy can knock us out now
    enemy_can_ko_after_recovery = post_recovery_hp <= max_opp_damage
    enemy_can_ko_now = our_current_hp <= max_opp_damage
    
    if enemy_can_ko_after_recovery or (we_are_slower and enemy_can_ko_now):
        return handle_toxic(battle)
    
    # If we have recover, HP is low enough, and we have PP, use it
    if my_pkmn.current_hp_fraction <= 0.6:
        return recover_move
    
    # Otherwise use handle_sleep
    return handle_toxic(battle)

def handle_sleep(battle):
    """
    Uses sleep powder if available and the Pokemon is either faster or will survive a hit.
    Otherwise returns the strongest move.
    
    Args:
        battle: Current battle state
        
    Returns:
        BattleOrder: Sleep move or strongest move
    """
    all_moves = Ply.possible_moves(battle)
    my_pkmn = battle.active_pokemon
    enem_pkmn = get_pokemon(battle.opponent_active_pokemon)
    
    # Check if opponent is already sleeping or has a status condition
    if enem_pkmn.status is not None:
        return handle_recover(battle)
    
    # Check if opponent is grass type
    if "grass" in [t.name.lower() for t in enem_pkmn.types]:
        return handle_recover(battle)
    
    # Check if any opponent Pokemon is already sleeping
    any_sleeping = False
    for pokemon in battle.opponent_team.values():
        if pokemon.status == Status.SLP:
            any_sleeping = True
            break
    
    if any_sleeping:
        return handle_recover(battle)
    
    # Check if we have a sleep move
    sleep_move = None
    for move in all_moves:
        if isinstance(move.order, Move) and ("sleep" in move.order.id.lower() or 
                                             "spore" in move.order.id.lower() or 
                                             "hypnosis" in move.order.id.lower()):
            sleep_move = move
            break
    
    # If no sleep move, use strongest move
    if not sleep_move:
        return handle_recover(battle)
    
    # Check if we're faster or can survive a hit
    our_speed = my_pkmn.stats.get("spe", 0)
    opp_speed = enem_pkmn.stats.get("spe", 0)
    we_are_faster = our_speed >= opp_speed
    
    # Calculate if we can survive a hit
    opp_damages = calc_damage(enem_pkmn, my_pkmn)
    our_hp = math.floor(my_pkmn.stats["hp"] * my_pkmn.current_hp_fraction)
    
    # Find max damage opponent can do
    max_opp_damage = 0
    if opp_damages:
        for damage_values in opp_damages.values():
            avg_damage = np.mean(damage_values)
            if avg_damage > max_opp_damage:
                max_opp_damage = avg_damage
    
    can_survive_hit = our_hp > max_opp_damage
    
    # If we're faster or can survive a hit, use sleep move
    if we_are_faster or can_survive_hit:
        return sleep_move
    
    # Otherwise use strongest move
    return handle_recover(battle)

def choose_move_strongest(battle):
    all_moves = Ply.possible_moves(battle)
    my_pkmn = battle.active_pokemon
    enem_pkmn = get_pokemon(battle.opponent_active_pokemon)
    damages = calc_damage(my_pkmn, enem_pkmn)
    max_damages = []

    for move in all_moves:
        # print(move.order, end = " ")
        if isinstance(move.order, Move):
            max_damages.append(np.mean(damages[move.order.id]))
        elif isinstance(move.order, Pokemon) and my_pkmn.status == Status.FNT:
            # select next Pokemon to send out, when current Pokemon has fainted
                # next_damages = calc_damage(move.order, enem_pkmn)
                # max_damages.append(max([np.mean(x) for x in next_damages.values()]))
            max_damages.append(0)
        else:
            max_damages.append(0)

    # print()
    # print("Damage of each choice ", max_damages)
    
    best_move = all_moves[np.argmax(max_damages)]
    
    # Exception for Venusaur - if best move is Power Whip, return Mega Drain instead
    if (my_pkmn.species == "venusaur" and 
        isinstance(best_move.order, Move) and 
        best_move.order.id.lower() == "powerwhip"):
        # Look for mega drain in possible moves
        for move in all_moves:
            if isinstance(move.order, Move) and move.order.id.lower() == "megadrain":
                return move
    
    return best_move

def best_move(battle):
    """
    Returns the strongest move if it can knock out the opponent,
    otherwise returns handle_sleep for better strategy.
    
    Args:
        battle: Current battle state
        
    Returns:
        BattleOrder: Strongest move that can KO or result from handle_sleep
    """
    all_moves = Ply.possible_moves(battle)
    my_pkmn = battle.active_pokemon
    enem_pkmn = get_pokemon(battle.opponent_active_pokemon)
    damages = calc_damage(my_pkmn, enem_pkmn)
    
    # Get the strongest move
    strongest_move = choose_move_strongest(battle)
    
    # Check if the strongest move can knock out the opponent
    if isinstance(strongest_move.order, Move):
        # Calculate enemy's current HP
        enemy_hp = math.floor(enem_pkmn.stats["hp"] * enem_pkmn.current_hp_fraction)
        
        # Get the average damage of the strongest move
        avg_damage = np.mean(damages[strongest_move.order.id])
        
        # If the move can KO the opponent, use it
        if avg_damage >= enemy_hp:
            return strongest_move
    
    # Otherwise, use handle_sleep for better strategic decisions
    return handle_sleep(battle)

def defense_potential(battle):
    """
    Returns a dictionary with each pokemon in the team and the damage it would take 
    if the current opponent played their most damaging move against it.
    
    Args:
        battle: Current battle state
        
    Returns:
        dict: Dictionary mapping each pokemon to the maximum damage it would take
    """
    result = {}
    opponent_pokemon = get_pokemon(battle.opponent_active_pokemon)
    
    # For each pokemon in our team
    for pokemon_id, pokemon in battle.team.items():
        # Skip fainted pokemon
        if pokemon.status == Status.FNT:
            continue
        
        # Get the moves and damage values from opponent to this pokemon
        damages = calc_damage(opponent_pokemon, pokemon)
        
        # Find the maximum average damage
        max_damage = 0
        if damages:
            for move_id, damage_values in damages.items():
                avg_damage = np.mean(damage_values)
                if avg_damage > max_damage:
                    max_damage = avg_damage
        
        # Calculate the damage as a fraction of total HP
        max_hp = pokemon.stats["hp"]
        damage_fraction = max_damage / max_hp
        
        # Store the result
        result[pokemon_id] = {
            "pokemon": pokemon,
            "max_damage": max_damage,
            "damage_fraction": damage_fraction,
            "remaining_hp_fraction": pokemon.current_hp_fraction - (damage_fraction if pokemon.current_hp_fraction > 0 else 0),
            "can_survive_hit": pokemon.current_hp_fraction * max_hp > max_damage
        }
    
    return result

def attack_potential(battle):
    """
    Returns a dictionary with each pokemon in our team and the damage it would do 
    to the current enemy pokemon if it uses its strongest move.
    
    Args:
        battle: Current battle state
        
    Returns:
        dict: Dictionary mapping each pokemon to information about its attack potential
    """
    result = {}
    enemy_pokemon = get_pokemon(battle.opponent_active_pokemon)
    
    # For each pokemon in our team
    for pokemon_id, pokemon in battle.team.items():
        # Skip fainted pokemon
        if pokemon.status == Status.FNT:
            continue
        
        # Get the moves and damage values from this pokemon to enemy
        damages = calc_damage(pokemon, enemy_pokemon)
        
        # Find the strongest move and its damage
        max_damage = 0
        best_move_id = None
        
        if damages:
            for move_id, damage_values in damages.items():
                avg_damage = np.mean(damage_values)
                if avg_damage > max_damage:
                    max_damage = avg_damage
                    best_move_id = move_id
        
        # Calculate enemy's HP
        enemy_hp = math.floor(enemy_pokemon.stats["hp"] * enemy_pokemon.current_hp_fraction)
        
        # Store the result
        result[pokemon_id] = {
            "pokemon": pokemon,
            "max_damage": max_damage,
            "damage_fraction": max_damage / enemy_pokemon.stats["hp"] if enemy_pokemon.stats["hp"] > 0 else 0,
            "best_move_id": best_move_id,
            "can_ko": max_damage >= enemy_hp,
            "speed": pokemon.stats.get("spe", 0),
            "faster_than_opponent": pokemon.stats.get("spe", 0) >= enemy_pokemon.stats.get("spe", 0)
        }
    
    return result

def advantage_ratio(battle, pokemon_id=None):
    """
    Calculates the ratio of maximum damage dealt to maximum damage taken
    for a specific Pokémon or the current active Pokémon.
    
    Args:
        battle: Current battle state
        pokemon_id: ID of the Pokémon to evaluate. If None, uses active Pokémon.
        
    Returns:
        float: Ratio of max damage dealt to max damage taken (>1 means advantage)
    """
    # If no pokemon_id provided, use active pokemon
    if pokemon_id is None:
        pokemon_id = next((pid for pid, pokemon in battle.team.items() 
                         if pokemon.species == battle.active_pokemon.species), None)
        if not pokemon_id:
            return 0.0  # No active pokemon found
    
    # Get damage potentials
    attack_data = attack_potential(battle)
    defense_data = defense_potential(battle)
    
    # If the pokemon isn't in both dictionaries, return 0
    if pokemon_id not in attack_data or pokemon_id not in defense_data:
        return 0.0
    
    # Get max damage dealt and taken
    max_damage_dealt = attack_data[pokemon_id]["max_damage"]
    max_damage_taken = defense_data[pokemon_id]["max_damage"]
    
    # Calculate the ratio, avoiding division by zero
    if max_damage_taken == 0:
        return float('inf') if max_damage_dealt > 0 else 1.0
    
    return max_damage_dealt / max_damage_taken

def should_switch(battle):
    """
    Determines if the current Pokémon should switch out and which Pokémon to switch to.
    Uses defense_potential and attack_potential to make intelligent switching decisions.
    If switching isn't recommended, returns the result of best_move instead.
    
    Args:
        battle: Current battle state
        
    Returns:
        BattleOrder: Switch order if switching is recommended, otherwise best_move result
    """    
    
    all_moves = Ply.possible_moves(battle)
    my_pkmn = battle.active_pokemon
    enem_pkmn = get_pokemon(battle.opponent_active_pokemon)
    
    # Find the current pokemon_id
    current_pokemon_id = None
    for pid, pokemon in battle.team.items():
        if pokemon.species == my_pkmn.species:
            current_pokemon_id = pid
            break
    
    # If current pokemon not found (should not happen), just use best move
    if not current_pokemon_id:
        return best_move(battle)
    
    # EXCEPTION: If our Pokémon is faster and can knock out the opponent in the next round,
    # directly use the strongest move
    attack_data = attack_potential(battle)
    if current_pokemon_id in attack_data:
        current_attack = attack_data[current_pokemon_id]
        if current_attack["faster_than_opponent"] and current_attack["can_ko"]:
            return choose_move_strongest(battle)
    
    # Step 1: Check if we need to switch based on advantage ratio or KO risk
    current_ratio = advantage_ratio(battle, current_pokemon_id)
    
    # Get defense data to check if we can be knocked out
    defense_data = defense_potential(battle)
    
    # Current pokemon can be knocked out this round if:
    # 1. It's slower than the opponent and can't survive a hit, or
    # 2. It can't survive a hit regardless of speed
    current_defense = defense_data.get(current_pokemon_id, {})
    current_hp = math.floor(my_pkmn.stats["hp"] * my_pkmn.current_hp_fraction)
    max_damage_taken = current_defense.get("max_damage", 0)
    our_speed = my_pkmn.stats.get("spe", 0)
    opp_speed = enem_pkmn.stats.get("spe", 0)
    
    can_be_ko_this_round = (current_hp <= max_damage_taken and 
                           (our_speed < opp_speed or current_hp <= max_damage_taken))
    
    # If neither condition is met, just use best move
    if current_ratio >= 0.8:
        return best_move(battle)
    
    # Get attack data for all our pokemon
    attack_data = attack_potential(battle)
    
    # Step 2: Find switches in the possible moves
    switch_options = []
    for move in all_moves:
        if isinstance(move.order, Pokemon) and move.order.species != my_pkmn.species:
            # Found a switch option
            for pid, pokemon in battle.team.items():
                if pokemon.species == move.order.species:
                    switch_options.append({
                        "pokemon_id": pid,
                        "pokemon": pokemon,
                        "move": move,
                        "advantage_ratio": advantage_ratio(battle, pid)
                    })
                    break
    
    # If no switch options (should not happen unless all fainted), use best move
    if not switch_options:
        return best_move(battle)
    
    # Step 3: First priority - faster pokemon that can KO opponent and not be KO'd
    for option in switch_options:
        pokemon_id = option["pokemon_id"]
        
        # Check if this pokemon is in both attack and defense data
        if pokemon_id not in attack_data or pokemon_id not in defense_data:
            continue
        
        # Check conditions:
        # 1. Faster than opponent
        # 2. Can KO opponent in one turn
        # 3. Won't be KO'd in one turn
        pokemon_attack = attack_data[pokemon_id]
        pokemon_defense = defense_data[pokemon_id]
        
        is_faster = pokemon_attack["faster_than_opponent"]
        can_ko = pokemon_attack["can_ko"]
        
        # Check if it can survive a hit
        pokemon = option["pokemon"]
        current_hp = math.floor(pokemon.stats["hp"] * pokemon.current_hp_fraction)
        max_damage_taken = pokemon_defense["max_damage"]
        can_survive = current_hp > max_damage_taken
        
        if is_faster and can_ko and can_survive:
            return option["move"]
    
    # Step 4: Sort remaining options by advantage ratio
    switch_options.sort(key=lambda x: x["advantage_ratio"], reverse=True)
    
    # Step 5: Consider each option in order
    for option in switch_options:
        pokemon_id = option["pokemon_id"]
        
        # Check if this pokemon is in both attack and defense data
        if pokemon_id not in attack_data or pokemon_id not in defense_data:
            continue
        
        # Get pokemon data
        pokemon = option["pokemon"]
        pokemon_defense = defense_data[pokemon_id]
        
        # Check speed
        is_slower = not attack_data[pokemon_id]["faster_than_opponent"]
        
        # Check if it will be knocked out in two turns
        current_hp = math.floor(pokemon.stats["hp"] * pokemon.current_hp_fraction)
        max_damage_taken = pokemon_defense["max_damage"]
        ko_in_two_turns = current_hp <= (2 * max_damage_taken)
        
        # Don't switch if slower and will be KO'd in two turns
        if is_slower and ko_in_two_turns:
            continue
        
        # Otherwise, switch to this pokemon
        return option["move"]
    
    # If no good switch found, use best move
    return best_move(battle)

class AIPly1(RPly):
    # set team you want to use
    TEAM = VENUSAUR

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # initialize any variables here

    def teampreview(self, battle):
        # function to choose lead pokemon
        mon_performance = {}

        # For each pokemon, compute value based on opponent team members
        # replace random.random() with evaluator
        for i, mon in enumerate(battle.team.values()):
            mon_performance[i] = np.mean(
                [
                    random.random() for opp in battle.opponent_team.values()
                ]
            )

        # We sort our mons by performance
        ordered_mons = sorted(mon_performance, key=lambda k: -mon_performance[k])

        # showdown's indexes start from 1
        return "/team " + "".join([str(i + 1) for i in ordered_mons])

    def choose_move(self, battle):
        my_pkmn = battle.active_pokemon
        pkmn = get_pokemon(battle.opponent_active_pokemon)
        damages = calc_damage(battle.active_pokemon, pkmn)
        # see below for how to collect some important data
        '''
        print(my_pkmn.current_hp, my_pkmn.current_hp_fraction, my_pkmn.species, my_pkmn.types, my_pkmn.stats)
        for name, move in my_pkmn.moves.items():
            print(name, move.accuracy, move.base_power, move.type, move.current_pp, end=" ")
        print()
        print(math.floor(pkmn.stats["hp"] * pkmn.current_hp_fraction), pkmn.current_hp_fraction, pkmn.species, pkmn.types, pkmn.stats)
        # operate on this object
        for name, move in pkmn.moves.items():
            print(name, move.accuracy, move.base_power, move.type, move.current_pp, end=" ")
        print()
        print(damages)
        '''
        # Implement function here, now returns handle_toxic
        return should_switch(battle)

class AIPly2(RPly):
    # set team you want to use
    TEAM = BLASTOISE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # initialize any variables here

    # define teampreview function

    def choose_move(self, battle):
        # Implement function here, currently returns strongest move
        return choose_move_strongest(battle)
        # old default
        return super().choose_move(battle) # random move

class AIPly3(RPly):
    # set team you want to use
    TEAM = VENUSAUR

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # initialize any variables here

    # define teampreview function

    def choose_move(self, battle):
        # Implement function here, currently returns strongest move
        return choose_move_strongest(battle)
        # old default
        return super().choose_move(battle) # random move

class AIPly4(RPly):
    # set team you want to use
    TEAM = PIKACHU

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # initialize any variables here

    # define teampreview function

    def choose_move(self, battle):
        # Implement function here, currently returns strongest move
        return choose_move_strongest(battle)
        # old default
        return super().choose_move(battle) # random move