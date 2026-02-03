# List of Edge Cases we are not handling

## All Classes

### Character summary page should display list of known spells ✅ FIXED

- ✅ A section on Spellcasting has been added listing all the available spells, level and their sources (class, feat, species, etc.)
- ✅ This includes all chosen cantrips and additional cantrips provided by feats, backgrounds, etc.
- ✅ It includes spell slot information for spell levels 1-9
- TODO: Add spells given by other features like species and species variants (when implemented)

### Repetitions:

- Repeated Skill Proficiency: users may select proficiency on skills which are then given in the Background or through some Feat. We need to recognize repeated proficiencies and offer the user alternatives from the original class skill list (not fixed)
- Repeated Cantrips: users may select Cantrips and then in a later feature get the same cantrip for free. We should allow users to specify an extra cantrip if that is the case. Example, user selects Light as a Cleric cantrip and then chooses the Light Domain which gives Light automatically.
- These can possibly solved before choosing the alignment, an extra and optional step in the wizard, allowing the user to fix these issues.

## Cleric

✅ Divine Order -> Protector : must grant proficiency with Martial weapons and Heavy Armor
✅ Divine Order -> Thaumaturge: grants one extra Cleric cantrip
✅ Light Domain -> gives the Light cantrip
Divine Order -> Thaumaturge: gives WIS bonus to Intelligence checks (Arcana or Religion), minimum of +1 (not fixed)

## Druid

Druid class and subclass files seems to mention many non-existant abilities (e.g Primal Strike). Need to regenerate data files.