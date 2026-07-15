"""Tests derived from real-world Kotlin patterns in Android/Compose projects."""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kotlin_doxygen.renderer import map_type, infer_type
from kotlin_doxygen.filter import filter_kotlin


class TestRealWorldPatterns(unittest.TestCase):
    """Tests based on patterns from the user's real-world project analysis."""

    # --- @OptIn annotation handling ---

    def test_optin_annotation_stripped(self):
        kt = '@OptIn(ExperimentalFoundationApi::class)\n@Composable\nfun FancyList(content: @Composable () -> Unit) {\n    content()\n}'
        output = filter_kotlin(kt, 'CustomElements.kt')
        self.assertNotIn('Unknown', output)
        self.assertNotIn('@OptIn', output)
        self.assertIn('public static void FancyList(Function content)', output)

    def test_optin_on_class(self):
        kt = '@OptIn(ExperimentalMaterial3Api::class)\nclass MyScreen {\n    @Composable\n    fun Content() {}\n}'
        output = filter_kotlin(kt, 'MyScreen.kt')
        self.assertNotIn('Unknown', output)
        self.assertIn('public class MyScreen', output)

    def test_suppress_annotation_stripped(self):
        kt = '@Suppress("unused")\nfun helper(): String = "hi"'
        output = filter_kotlin(kt, 'Helper.kt')
        self.assertNotIn('@Suppress', output)
        self.assertNotIn('Unknown', output)
        self.assertIn('public static String helper()', output)

    def test_requiresapi_annotation_stripped(self):
        kt = '@RequiresApi(Build.VERSION_CODES.S)\nfun newApiCall() {}'
        output = filter_kotlin(kt, 'ApiCompat.kt')
        self.assertNotIn('@RequiresApi', output)
        self.assertNotIn('Unknown', output)

    def test_suppresslint_stripped(self):
        kt = '@SuppressLint("Recycle")\nfun cleanup() {}'
        output = filter_kotlin(kt, 'Cleanup.kt')
        self.assertNotIn('@SuppressLint', output)
        self.assertNotIn('Unknown', output)

    # --- inline / crossinline / noinline ---

    def test_inline_function(self):
        kt = 'inline fun <T> measure(block: () -> T): T {\n    return block()\n}'
        output = filter_kotlin(kt, 'Perf.kt')
        self.assertNotIn('inline', output)
        self.assertIn('public static <T> T measure(Function block)', output)

    def test_noinline_parameter(self):
        kt = 'fun <T> run(items: List<T>, noinline key: (T) -> Any?) {\n    // body\n}'
        output = filter_kotlin(kt, 'Runner.kt')
        self.assertNotIn('noinline', output)
        self.assertIn('Function key', output)

    def test_crossinline_parameter(self):
        kt = 'fun <T> build(crossinline builder: () -> T): T {\n    return builder()\n}'
        output = filter_kotlin(kt, 'Builder.kt')
        self.assertNotIn('crossinline', output)
        self.assertIn('Function builder', output)

    def test_inline_with_complex_callback(self):
        kt = 'inline fun <T> draggableItems(\n    items: List<T>,\n    noinline key: ((item: T) -> Any)? = null,\n    crossinline contentType: (item: T) -> Any? = { null },\n    crossinline itemContent: @Composable LazyItemScope.(item: T) -> Unit\n) {\n    // body\n}'
        output = filter_kotlin(kt, 'DraggableLazyList.kt')
        self.assertNotIn('noinline', output)
        self.assertNotIn('crossinline', output)
        self.assertNotIn('->', output)
        self.assertIn('public static <T> void draggableItems(List<T> items, Function key, Function contentType, Function itemContent)', output)

    # --- Extension functions ---

    def test_simple_extension_function(self):
        kt = 'fun String.cleanUp(suffix: String): String {\n    return this.trim() + suffix\n}'
        output = filter_kotlin(kt, 'StringExt.kt')
        self.assertIn('public static String cleanUp(String receiver, String suffix)', output)

    def test_generic_extension_function(self):
        kt = 'fun <T> List<T>.secondOrNull(): T? {\n    return if (size > 1) this[1] else null\n}'
        output = filter_kotlin(kt, 'ListExt.kt')
        self.assertIn('public static <T> T secondOrNull(List<T> receiver)', output)

    def test_extension_function_with_vararg(self):
        kt = 'fun <T> List<T>.replaceMany(vararg pairs: Pair<T, T>): List<T> =\n    pairs.fold(this) { acc, (old, new) -> acc.map { if (it == old) new else it } }'
        output = filter_kotlin(kt, 'Utils.kt')
        self.assertIn('public static <T> List<T> replaceMany(List<T> receiver, Pair<T, T> pairs)', output)
        self.assertNotIn('pairs.fold', output)
        self.assertNotIn('->', output)

    def test_extension_property(self):
        kt = 'val String.firstChar: Char get() = this[0]'
        output = filter_kotlin(kt, 'StringExt.kt')
        self.assertIn('public static final char firstChar', output)

    # --- Type normalization ---

    def test_byte_array(self):
        self.assertEqual(map_type('ByteArray'), 'byte[]')

    def test_char_array(self):
        self.assertEqual(map_type('CharArray'), 'char[]')

    def test_int_array(self):
        self.assertEqual(map_type('IntArray'), 'int[]')

    def test_long_array(self):
        self.assertEqual(map_type('LongArray'), 'long[]')

    def test_float_array(self):
        self.assertEqual(map_type('FloatArray'), 'float[]')

    def test_double_array(self):
        self.assertEqual(map_type('DoubleArray'), 'double[]')

    def test_boolean_array(self):
        self.assertEqual(map_type('BooleanArray'), 'boolean[]')

    def test_array_out_wildcard(self):
        self.assertEqual(map_type('Array<out X509Certificate>'), 'X509Certificate[]')

    def test_mutable_list(self):
        self.assertEqual(map_type('MutableList<String>'), 'List<String>')

    def test_mutable_map(self):
        self.assertEqual(map_type('MutableMap<String, Int>'), 'Map<String, Integer>')

    def test_mutable_set(self):
        self.assertEqual(map_type('MutableSet<String>'), 'Set<String>')

    def test_function_type(self):
        self.assertEqual(map_type('(Int, String) -> Unit'), 'Function')

    def test_pair_type(self):
        # Pair should be preserved as a readable type
        result = map_type('Pair<String, Int>')
        self.assertIn('Pair', result)
        self.assertIn('String', result)
        self.assertIn('Integer', result)

    def test_nullable_type_stripped(self):
        self.assertEqual(map_type('String?'), 'String')

    def test_nullable_generic(self):
        self.assertEqual(map_type('List<String>?'), 'List<String>')

    # --- Same-name superclass ---

    def test_same_name_imported_superclass(self):
        kt = 'package com.test\nimport androidx.lifecycle.ViewModel\n\nclass ViewModel : ViewModel() {\n}'
        output = filter_kotlin(kt, 'ViewModel.kt')
        self.assertIn('extends androidx.lifecycle.ViewModel', output)
        self.assertNotIn('extends ViewModel()', output)

    def test_same_name_connection_service(self):
        kt = 'package com.test\nimport android.telecom.ConnectionService\n\nclass ConnectionService : ConnectionService() {\n}'
        output = filter_kotlin(kt, 'ConnectionService.kt')
        self.assertIn('extends android.telecom.ConnectionService', output)

    # --- sealed / data class ---

    def test_sealed_class(self):
        kt = 'sealed class Result {\n    data class Success(val data: String) : Result()\n    data class Error(val message: String) : Result()\n}'
        output = filter_kotlin(kt, 'Result.kt')
        self.assertIn('public class Result', output)
        # data classes should still be recognized as classes
        self.assertIn('public class Success', output)
        self.assertIn('public class Error', output)

    def test_data_class(self):
        kt = 'data class User(val name: String, val age: Int)'
        output = filter_kotlin(kt, 'User.kt')
        self.assertIn('public class User', output)
        self.assertIn('public final String name', output)
        self.assertIn('public final int age', output)

    # --- Delegated properties ---

    def test_delegated_by_lazy(self):
        kt = 'class Config {\n    val expensive: String by lazy { computeValue() }\n}'
        output = filter_kotlin(kt, 'Config.kt')
        self.assertIn('public final String expensive', output)

    def test_delegated_mutableStateOf(self):
        kt = 'class State {\n    var count by mutableStateOf(0)\n}'
        output = filter_kotlin(kt, 'State.kt')
        self.assertIn('public int count', output)

    def test_delegated_mutableIntStateOf(self):
        kt = 'class State {\n    var selected by mutableIntStateOf(0)\n}'
        output = filter_kotlin(kt, 'State.kt')
        self.assertIn('public int selected', output)

    # --- Companion object ---

    def test_companion_object_factory(self):
        kt = 'class Container {\n    companion object Factory {\n        fun create(): Container = Container()\n    }\n}'
        output = filter_kotlin(kt, 'Container.kt')
        self.assertIn('public static Container create()', output)

    def test_companion_object_without_name(self):
        kt = 'class Utils {\n    companion object {\n        fun helper() {}\n    }\n}'
        output = filter_kotlin(kt, 'Utils.kt')
        self.assertIn('public static void helper()', output)

    # --- Top-level wrappers ---

    def test_top_level_function_wrapped(self):
        kt = 'fun greet(name: String): String {\n    return "Hello, $name"\n}'
        output = filter_kotlin(kt, 'Greeting.kt')
        self.assertIn('public class GreetingKt', output)
        self.assertIn('public static String greet(String name)', output)

    def test_top_level_val_wrapped(self):
        kt = 'val APP_VERSION = "1.0.0"'
        output = filter_kotlin(kt, 'Constants.kt')
        self.assertIn('public class ConstantsKt', output)
        self.assertIn('public static final String APP_VERSION', output)

    # --- External functions ---

    def test_external_function(self):
        kt = 'external fun nativeCall(): Int'
        output = filter_kotlin(kt, 'Native.kt')
        self.assertIn('native', output)
        self.assertIn('int nativeCall()', output)

    # --- Where clause ---

    def test_where_clause_stripped(self):
        kt = 'class Box<T>(val value: T) where T : Any {\n    fun unwrap(): T = value\n}'
        output = filter_kotlin(kt, 'Box.kt')
        self.assertNotIn('where', output)
        self.assertIn('public class Box<T>', output)

    # --- Inheritance ---

    def test_multiline_inheritance(self):
        kt = 'class FancyService :\n    BaseService(),\n    Closeable {\n}'
        output = filter_kotlin(kt, 'FancyService.kt')
        self.assertIn('extends BaseService', output)
        self.assertIn('implements Closeable', output)

    # --- @file directive ---

    def test_file_directive(self):
        kt = 'package com.example'
        output = filter_kotlin(kt, 'File.kt')
        self.assertTrue(output.startswith('/** @file */'))


if __name__ == '__main__':
    unittest.main()
