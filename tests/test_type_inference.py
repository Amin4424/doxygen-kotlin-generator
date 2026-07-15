"""Test type inference patterns."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kotlin_doxygen.renderer import infer_type

test_cases = [
    ('TestNetworkMonitor()', 'TestNetworkMonitor'),
    ('TestUserDataRepository()', 'TestUserDataRepository'),
    ('CompositeUserNewsResourceRepository(TestNewsRepository(), TestUserDataRepository())', 'CompositeUserNewsResourceRepository'),
    ('createComposeRule()', 'Object'),  # Can't infer external
    ('NavigationState(startKey, topLevelStack, subStacks)', 'NavigationState'),
    ('Navigator(navigationState)', 'Navigator'),
    ('listOf(1, 2, 3)', 'List'),
    ('mutableListOf<String>()', 'List'),
    ('arrayOf(1, 2, 3)', 'Array'),
    ('setOf(1, 2, 3)', 'Set'),
    ('emptyList<String>()', 'List'),
    ('emptyMap<String, Int>()', 'Map'),
    ('buildList { add(1) }', 'List'),
    ('buildMap { put("a", 1) }', 'Map'),
    ('listOfNotNull(1, null, 3)', 'List'),
    ('sequenceOf(1, 2, 3)', 'Sequence'),
    ('flowOf(1, 2, 3)', 'Flow'),
    ('channelOf(1, 2, 3)', 'Channel'),
    ('runBlocking { 1 }', 'Object'),
    ('withContext(Dispatchers.IO) { 1 }', 'Object'),
    ('MutableStateFlow(0)', 'MutableStateFlow<Integer>'),
    ('StateFlow(0)', 'StateFlow<Integer>'),
    ('mutableStateOf(0)', 'int'),
    ('mutableIntStateOf(0)', 'int'),
    ('mutableFloatStateOf(0f)', 'float'),
    ('remember { mutableStateOf(0) }', 'int'),
    ('derivedStateOf { 1 }', 'State'),
    ('snapshotFlow { 1 }', 'Flow'),
    ('produceState(0) { 1 }', 'State'),
]

for kt, expected in test_cases:
    result = infer_type(kt)
    status = 'PASS' if result == expected else 'FAIL'
    print(f'{status}: {kt} -> {result} (expected: {expected})')
