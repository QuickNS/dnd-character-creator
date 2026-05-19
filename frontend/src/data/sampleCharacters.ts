export interface SampleCharacter {
  id: string;
  name: string;
  species: string;
  gender: "male" | "female";
  characterClass: string;
  subclass: string;
  /** Matches the filename stem under /images/classes/ (e.g. "barbarian") */
  classKey: string;
  flavor: string;
}

export const SAMPLE_CHARACTERS: SampleCharacter[] = [
  {
    id: "barbarian",
    name: "Kragor Stonefist",
    species: "Goliath",
    gender: "male",
    characterClass: "Barbarian",
    subclass: "Path of the Berserker",
    classKey: "barbarian",
    flavor:
      "He doesn't count the enemies before the battle. He counts them after.",
  },
  {
    id: "bard",
    name: "Vexa Nightsong",
    species: "Tiefling",
    gender: "female",
    characterClass: "Bard",
    subclass: "College of Valor",
    classKey: "bard",
    flavor:
      "She walked into the dragon's lair with a lute and walked out with a ballad.",
  },
  {
    id: "cleric",
    name: "Torvin Ironvow",
    species: "Dwarf",
    gender: "male",
    characterClass: "Cleric",
    subclass: "War Domain",
    classKey: "cleric",
    flavor:
      "His god is the sound of steel. His prayers are answered in broken shields.",
  },
  {
    id: "druid",
    name: "Sylara Dawnwhisper",
    species: "Elf",
    gender: "female",
    characterClass: "Druid",
    subclass: "Circle of the Moon",
    classKey: "druid",
    flavor: "The forest doesn't fear her. The forest is her.",
  },
  {
    id: "fighter",
    name: "Valdris Ashenbrow",
    species: "Human",
    gender: "male",
    characterClass: "Fighter",
    subclass: "Battle Master",
    classKey: "fighter",
    flavor: "A scarred veteran who turns every duel into a chess match.",
  },
  {
    id: "monk",
    name: "Scale-of-Jade",
    species: "Dragonborn",
    gender: "male",
    characterClass: "Monk",
    subclass: "Warrior of Mercy",
    classKey: "monk",
    flavor: "He heals with one hand and silences with the other.",
  },
  {
    id: "paladin",
    name: "Seraphel Ashveil",
    species: "Tiefling",
    gender: "female",
    characterClass: "Paladin",
    subclass: "Oath of Vengeance",
    classKey: "paladin",
    flavor:
      "The wicked fear her not because of her sword, but because she never forgets a name.",
  },
  {
    id: "ranger",
    name: "Senna Nightbough",
    species: "Elf",
    gender: "female",
    characterClass: "Ranger",
    subclass: "Gloom Stalker",
    classKey: "ranger",
    flavor: "By the time you hear the arrow, she's already gone.",
  },
  {
    id: "rogue",
    name: "Zara'lyn",
    species: "Drow",
    gender: "female",
    characterClass: "Rogue",
    subclass: "Assassin",
    classKey: "rogue",
    flavor: "She was never in the room. That's what makes it so unsettling.",
  },
  {
    id: "sorcerer",
    name: "Seraphine Dusk",
    species: "Aasimar",
    gender: "female",
    characterClass: "Sorcerer",
    subclass: "Draconic Sorcery",
    classKey: "sorcerer",
    flavor: "She speaks softly and carries a staff that ends kingdoms.",
  },
  {
    id: "warlock",
    name: "Grax the Bound",
    species: "Orc",
    gender: "male",
    characterClass: "Warlock",
    subclass: "Fiend Patron",
    classKey: "warlock",
    flavor: "He made a deal. He has not yet decided if he regrets it.",
  },
  {
    id: "wizard",
    name: "Pip Runebright",
    species: "Gnome",
    gender: "male",
    characterClass: "Wizard",
    subclass: "Evoker",
    classKey: "wizard",
    flavor:
      "Small, meticulous, and capable of erasing a village with a gesture.",
  },
];
