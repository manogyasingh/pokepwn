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
    return best_move

class AIPly1(RPly):
    # set team you want to use
    TEAM = CHARIZARD

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
        # Implement function here, currently returns strongest move
        return choose_move_strongest(battle)
        # old default
        return super().choose_move(battle) # random move

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