import random
import argparse
import sys
from abc import ABC, abstractmethod
from typing import List, Type, Optional


class Ability(ABC):
    name: str
    activation_chance: float = 0.25

    @abstractmethod
    def on_attack(self, attacker: 'Character', base_attack: int) -> int:
        return base_attack

    @abstractmethod
    def on_defend(self, defender: 'Character', incoming_damage: int) -> int:
        return incoming_damage

    @abstractmethod
    def on_damage_taken(self, defender: 'Character', damage: int, previouse_health: int, current_health: int) -> int:
        return current_health


class DamageReduction(Ability):
    name = "Damage Reduction"

    def on_attack(self, attacker: 'Character', base_attack: int) -> int:
        return base_attack

    def on_defend(self, defender: 'Character', incoming_damage: int) -> int:
        if random.random() < self.activation_chance:
            print(f"{defender.name} activates {self.name} - takes only half damage")
            return incoming_damage // 2
        return incoming_damage

    def on_damage_taken(self, defender: 'Character', damage: int, previous_health: int, current_health: int) -> int:
        return current_health


class PowerStrike(Ability):
    name = "Power Strike"

    def on_attack(self, attacker: 'Character', base_attack: int) -> int:
        if random.random() < self.activation_chance:
            print(f"{attacker.name} activates {self.name} - attack power increase by 50%")
            return base_attack * 3 // 2
        return base_attack

    def on_defend(self, defender: 'Character', incoming_damage: int) -> int:
        return incoming_damage

    def on_damage_taken(self, defender: 'Character', damage: int, previouse_health: int, current_health: int) -> int:
        return current_health


class SecondWind(Ability):
    name = "Second Wind"

    def on_attack(self, attacker: 'Character', base_attack: int) -> int:
        return base_attack

    def on_defend(self, defender: 'Character', incoming_damage: int) -> int:
        return incoming_damage

    def on_damage_taken(self, defender: 'Character', damage: int, previous_health: int, current_health: int) -> int:
        if previous_health >= 30 and current_health <30 and current_health > 0:
            if random.random() < self.activation_chance:
                heal = 5
                new_health = min(100, current_health + heal)
                print(f"{defender.name} activates {self.name} - heals {heal} health")
                return new_health
        return current_health


class Vampiric(Ability):
    name = "Vampiric"

    def on_attack(self, attacker: 'Character', base_attack: int) -> int:
        if random.random() < self.activation_chance:
            print(f"{attacker.name} activates {self.name} - will heal for half damage dealt")
            attacker._vampiric_active = True
        return base_attack

    def on_defend(self, defender: 'Character', incoming_damage: int) -> int:
        return incoming_damage

    def on_damage_taken(self, defender: 'Character', damage: int, previous_health: int, current_health: int) -> int:
        return current_health


ABILITY_REGISTRY: List[Type[Ability]] = [DamageReduction, PowerStrike, SecondWind]


def register_ability(ability_class: Type[Ability]) -> None:
    ABILITY_REGISTRY.append(ability_class)


def random_ability() -> Ability:
    return random.choice(ABILITY_REGISTRY)()


class Character:
    def __init__(self, name: str, attack: int, defense: int, ability: Optional[Ability] = None):
        self.name = name
        self.attack_power = attack
        self.defense_power = defense
        self.health = 100
        self.ability = ability
        self._vampiric_active = False

    def __str__(self) -> str:
        return f"{self.name}: attack={self.attack_power}, defense={self.defense_power}"

    def reset_for_new_simulation(self, attack: int, defense: int, ability: Optional[Ability] = None) -> None:
        self.attack_power = attack
        self.defense_power = defense
        self.health = 100
        self.ability = ability
        self._vampiric_active = False

    def attack(self, other: 'Character', verbose: bool = True) -> bool:
        base_attack = self.attack_power
        if self.ability:
            base_attack = self.ability.on_attack(self, base_attack)

        raw_damage = base_attack - other.defense_power
        if raw_damage < 0:
            raw_damage = 0

        if other.ability:
            raw_damage = other.ability.on_defend(other, raw_damage)

        previous_health = other.health
        other.health -= raw_damage
        if verbose:
            print(f"  {self.name} attacks - deals {raw_damage} damage")

        if other.ability:
            new_health = other.ability.on_damage_taken(other, raw_damage,previous_health, other.health)
            other.health = new_health

        if self._vampiric_active and raw_damage > 0:
            heal_amount = raw_damage // 2
            self.health = min(100, self.health + heal_amount)
            if verbose:
                print(f"  {self.name} heals {heal_amount} health from Vampiric")
            self._vampiric_active = False

        other.health = min(100, other.health)
        self.health = min(100, self.health)

        if verbose:
            print(f"  {other.name} has {other.health} health")

        return other.health <= 0


def run_duel(char1: Character, char2: Character, per_round_abilities: bool = False, verbose: bool = True) -> int:
    attacker, defender = (char1, char2) if random.random() < 0.5 else (char2, char1)
    round_num = 1

    if verbose:
        print("\n--- Duel Start ---")
        print(char1)
        print(char2)
        print(f"{attacker.name} attacks first!\n")

    while True:
        if verbose:
            print(f"Round {round_num}:")

        if per_round_abilities:
            char1.ability = random_ability()
            char2.ability = random_ability()
            if verbose:
                print(f"  {char1.name} gains ability: {char1.ability.name if char1.ability else 'None'}")
                print(f"  {char2.name} gains ability: {char2.ability.name if char2.ability else 'None'}")

        if verbose:
            print(f"  {attacker.name}'s turn:")
        if attacker.attack(defender, verbose):
            winner = attacker
            break

        attacker, defender = defender, attacker

        if verbose:
            print(f"  {attacker.name}'s turn:")
        if attacker.attack(defender, verbose):
            winner = attacker
            break

        attacker, defender = defender, attacker
        round_num += 1
        if verbose:
            print()

    if verbose:
        print(f"\n{winner.name} won!\n")
    return 1 if winner is char1 else 2


def run_multiple_simulations(n: int, per_round: bool = False) -> None:
    wins1 = 0
    wins2 = 0

    for i in range(n):
        attack1 = random.randint(15, 20)
        defense1 = random.randint(10, 15)
        attack2 = random.randint(15, 20)
        defense2 = random.randint(10, 15)

        if per_round:
            ability1 = None
            ability2 = None
        else:
            ability1 = random_ability()
            ability2 = random_ability()

        c1 = Character("Character 1", attack1, defense1, ability1)
        c2 = Character("Character 2", attack2, defense2, ability2)

        winner = run_duel(c1, c2, per_round_abilities=per_round, verbose=False)
        if winner == 1:
            wins1 += 1
        else:
            wins2 += 1

    total = wins1 + wins2
    print(f"\nAfter {total} simulations:")
    print(f"Character 1 wins: {wins1} ({wins1/total*100:.1f}%)")
    print(f"Character 2 wins: {wins2} ({wins2/total*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Turn-based duel game simulation")
    parser.add_argument("--runs", type=int, default=1, help="Number of simulations to run (default 1, prints detailed output if 1)")
    parser.add_argument("--mode", choices=["fixed", "per_round"], default="fixed", help="Ability assignment mode: fixed at start or per round")
    parser.add_argument("--add-fourth", action="store_true", help="Add a fourth ability (Vampiric) to the ability pool")

    args = parser.parse_args()

    if args.add_fourth:
        register_ability(Vampiric)
        print("Fourth ability 'Vampiric' added to the game.")

    if args.runs == 1:
        attack1 = random.randint(15, 20)
        defense1 = random.randint(10, 15)
        attack2 = random.randint(15, 20)
        defense2 = random.randint(10, 15)

        if args.mode == "fixed":
            ability1 = random_ability()
            ability2 = random_ability()
        else:
            ability1 = None
            ability2 = None

        char1 = Character("Character 1", attack1, defense1, ability1)
        char2 = Character("Character 2", attack2, defense2, ability2)

        print("Initial stats:")
        print(char1)
        print(char2)
        if args.mode == "fixed":
            print(f"Character 1 ability: {ability1.name if ability1 else 'None'}")
            print(f"Character 2 ability: {ability2.name if ability2 else 'None'}")

        run_duel(char1, char2, per_round_abilities=(args.mode == "per_round"), verbose=True)
    else:
        run_multiple_simulations(args.runs, per_round=(args.mode == "per_round"))


if __name__ == "__main__":
    main()