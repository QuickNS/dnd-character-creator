#!/usr/bin/env python3
"""
Unit tests for the Light Domain cleric subclass.
Tests all features, effects, and mechanics specific to the Light Domain.
"""

import pytest
from modules.character_builder import CharacterBuilder


@pytest.fixture
def light_cleric_builder():
    """Fixture providing a fresh CharacterBuilder with Light Domain cleric setup"""
    builder = CharacterBuilder()
    builder.set_species('Human')
    builder.set_class('Cleric', 3)
    builder.set_subclass('Light Domain')
    return builder


class TestLightDomain:
    """Test Light Domain subclass implementation"""
    
    def test_light_domain_effects(self, light_cleric_builder):
        """Test Light Domain specific effects"""
        char_data = light_cleric_builder.character_data
        
        # Check bonus cantrip (Light)
        cantrips = char_data['spells']['cantrips']
        assert 'Light' in cantrips
        
        # Check domain spells
        prepared_spells = char_data['spells']['prepared']
        assert 'Burning Hands' in prepared_spells
        assert 'Faerie Fire' in prepared_spells

    def test_light_domain_features(self, light_cleric_builder):
        """Test Light Domain specific features are present"""
        char_data = light_cleric_builder.character_data
        subclass_features = char_data['features']['subclass']
        feature_names = [f['name'] for f in subclass_features]
        
        # Light Domain should have these features at level 3
        assert 'Bonus Cantrip' in feature_names
        assert 'Light Domain Spells' in feature_names
        assert 'Warding Flare' in feature_names

    def test_bonus_cantrip_feature(self, light_cleric_builder):
        """Test Light Domain bonus cantrip feature"""
        char_data = light_cleric_builder.character_data
        
        # Should have Light cantrip from the bonus cantrip feature
        cantrips = char_data['spells']['cantrips']
        assert 'Light' in cantrips
        
        # Check feature is listed
        subclass_features = char_data['features']['subclass']
        bonus_cantrip_feature = None
        for feature in subclass_features:
            if feature['name'] == 'Bonus Cantrip':
                bonus_cantrip_feature = feature
                break
        
        assert bonus_cantrip_feature is not None
        assert 'Light' in bonus_cantrip_feature['description']

    def test_warding_flare_feature(self, light_cleric_builder):
        """Test Warding Flare feature"""
        char_data = light_cleric_builder.character_data
        subclass_features = char_data['features']['subclass']
        
        warding_flare_feature = None
        for feature in subclass_features:
            if feature['name'] == 'Warding Flare':
                warding_flare_feature = feature
                break
        
        assert warding_flare_feature is not None
        description = warding_flare_feature['description']
        assert 'reaction' in description.lower()
        assert 'disadvantage' in description.lower()

    def test_light_domain_spell_progression(self, light_cleric_builder):
        """Test Light Domain spell progression at different levels"""
        # At level 3, should have level 3 domain spells
        char_data = light_cleric_builder.character_data
        prepared_spells = char_data['spells']['prepared']
        assert 'Burning Hands' in prepared_spells
        assert 'Faerie Fire' in prepared_spells
        
        # Level up to 5, should gain level 5 domain spells
        light_cleric_builder.set_class('Cleric', 5)
        char_data = light_cleric_builder.character_data
        prepared_spells = char_data['spells']['prepared']
        
        # Should still have level 3 spells
        assert 'Burning Hands' in prepared_spells
        assert 'Faerie Fire' in prepared_spells
        
        # Should now have level 5 domain spells
        assert 'Scorching Ray' in prepared_spells
        assert 'See Invisibility' in prepared_spells