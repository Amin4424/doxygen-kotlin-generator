import unittest
import sys
import os
import io
from unittest.mock import patch

# Add package directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kotlin_doxygen.parser import split_params
from kotlin_doxygen.renderer import map_type, infer_type, translate_param_list
from kotlin_doxygen.filter import filter_kotlin
from kotlin_doxygen.cli import main

class TestKotlinDoxygen(unittest.TestCase):

    def test_map_type(self):
        self.assertEqual(map_type("Int"), "int")
        self.assertEqual(map_type("Long"), "long")
        self.assertEqual(map_type("Boolean?"), "boolean")
        self.assertEqual(map_type("ArrayList<String>"), "ArrayList<String>")
        self.assertEqual(map_type("ByteArray"), "byte[]")
        self.assertEqual(map_type("CharArray"), "char[]")
        self.assertEqual(map_type("Array<out X509Certificate>"), "X509Certificate[]")
        self.assertEqual(map_type("MutableList<String>"), "List<String>")
        self.assertEqual(map_type("Map<String, Int>"), "Map<String, Integer>")
        self.assertEqual(map_type("(Int, String) -> Unit"), "Function")
        self.assertEqual(map_type(""), "Object")

    def test_infer_type(self):
        self.assertEqual(infer_type("true"), "boolean")
        self.assertEqual(infer_type("false"), "boolean")
        self.assertEqual(infer_type('"hello"'), "String")
        self.assertEqual(infer_type('"""multiline"""'), "String")
        self.assertEqual(infer_type("123"), "int")
        self.assertEqual(infer_type("123L"), "long")
        self.assertEqual(infer_type("1.23"), "double")
        self.assertEqual(infer_type("1.23f"), "float")
        self.assertEqual(infer_type("ArrayList<String>()"), "ArrayList")
        self.assertEqual(infer_type("listOf(1, 2)"), "List")
        self.assertEqual(infer_type("mutableStateOf(1)"), "int")
        self.assertEqual(infer_type("remember { mutableStateOf(false) }"), "boolean")

    def test_split_params(self):
        self.assertEqual(split_params("a: Int, b: String"), ["a: Int", "b: String"])
        self.assertEqual(split_params("map: Map<String, Int>, name: String"), ["map: Map<String, Int>", "name: String"])
        self.assertEqual(split_params("x: Int = 0, y: Int = 1"), ["x: Int = 0", "y: Int = 1"])
        self.assertEqual(
            split_params("items: List<T>, key: ((item: T) -> Any)? = null, content: (T) -> Unit"),
            ["items: List<T>", "key: ((item: T) -> Any)? = null", "content: (T) -> Unit"],
        )

    def test_translate_param_list(self):
        self.assertEqual(translate_param_list("a: Int, b: String?"), "int a, String b")
        self.assertEqual(translate_param_list("val accp: Long, virtualAor: String? = null"), "long accp, String virtualAor")
        self.assertEqual(translate_param_list("map: Map<String, Int>"), "Map<String, Integer> map")
        self.assertEqual(
            translate_param_list("noinline contentType: (item: String) -> Any? = { null }"),
            "Function contentType",
        )
        self.assertEqual(
            translate_param_list("crossinline itemContent: @Composable LazyItemScope.(item: String) -> Unit"),
            "Function itemContent",
        )

    def test_filter_kotlin_basic(self):
        kt_code = """
        package com.test
        import java.util.*
        
        /**
         * Docs for MyClass.
         */
        class MyClass(val id: Int, var name: String?) {
            fun doWork(item: String): Boolean {
                return true
            }
        }
        """
        output = filter_kotlin(kt_code, "MyClass.kt")
        
        # Verify docs are preserved
        self.assertIn("Docs for MyClass", output)
        # Verify class maps to java
        self.assertIn("public class MyClass", output)
        # Verify primary constructor fields are injected
        self.assertIn("public final int id;", output)
        self.assertIn("public String name;", output)
        # Verify constructor method is injected
        self.assertIn("public MyClass(int id, String name)", output)
        # Verify doWork is translated to Java style
        self.assertIn("public boolean doWork(String item)", output)

    def test_filter_kotlin_companion(self):
        kt_code = """
        class Container {
            companion object Factory {
                fun create(): Container = Container()
            }
        }
        """
        output = filter_kotlin(kt_code, "Container.kt")
        # Factory method inside companion should be static
        self.assertIn("public static Container create()", output)

    def test_filter_kotlin_extension_function(self):
        kt_code = """
        fun String.cleanUp(suffix: String): String {
            return this.trim() + suffix
        }
        """
        output = filter_kotlin(kt_code, "StringExt.kt")
        # Extension should become static method with receiver as first parameter
        self.assertIn("public static String cleanUp(String receiver, String suffix)", output)

    def test_filter_kotlin_generic_extension_function_with_lambda_body(self):
        kt_code = """
        inline fun <T> List<T>.replaceMany(vararg pairs: Pair<T, T>): List<T> =
            pairs.fold(this) { acc, (old, new) -> acc.map { if (it == old) new else it } }
        """
        output = filter_kotlin(kt_code, "Utils.kt")
        self.assertIn("public static <T> List<T> replaceMany(List<T> receiver, Pair<T, T> pairs) {}", output)
        self.assertNotIn("->", output)
        self.assertNotIn("pairs.fold", output)

    def test_filter_kotlin_strips_annotations_without_unknown_classes(self):
        kt_code = """
        @OptIn(ExperimentalFoundationApi::class)
        @Composable
        fun FancyList(content: @Composable () -> Unit) {
            content()
        }
        """
        output = filter_kotlin(kt_code, "CustomElements.kt")
        self.assertIn("public static void FancyList(Function content)", output)
        self.assertNotIn("@OptIn", output)
        self.assertNotIn("Unknown", output)

    def test_filter_kotlin_inline_callback_modifiers(self):
        kt_code = """
        inline fun <T> draggableItems(
            items: List<T>,
            noinline key: ((item: T) -> Any)? = null,
            crossinline contentType: (item: T) -> Any? = { null },
            crossinline itemContent: @Composable LazyItemScope.(item: T) -> Unit
        ) {}
        """
        output = filter_kotlin(kt_code, "DraggableLazyList.kt")
        self.assertIn(
            "public static <T> void draggableItems(List<T> items, Function key, Function contentType, Function itemContent)",
            output,
        )
        self.assertNotIn("noinline", output)
        self.assertNotIn("crossinline", output)
        self.assertNotIn("->", output)

    def test_filter_kotlin_class_generics_and_where_clause(self):
        kt_code = """
        class Box<T>(val value: T) where T : Any {
            fun unwrap(): T = value
        }
        """
        output = filter_kotlin(kt_code, "Box.kt")
        self.assertIn("public class Box<T>", output)
        self.assertIn("public final T value;", output)
        self.assertIn("public Box(T value)", output)
        self.assertNotIn("where", output)

    def test_filter_kotlin_multiline_inheritance(self):
        kt_code = """
        class FancyService :
            BaseService(),
            Closeable {
        }
        """
        output = filter_kotlin(kt_code, "FancyService.kt")
        self.assertIn("public class FancyService extends BaseService implements Closeable", output)

    def test_filter_kotlin_delegated_state_inference(self):
        kt_code = """
        class ScreenState {
            var selected by mutableIntStateOf(0)
            var enabled by remember { mutableStateOf(false) }
        }
        """
        output = filter_kotlin(kt_code, "ScreenState.kt")
        self.assertIn("public int selected;", output)
        self.assertIn("public boolean enabled;", output)

    def test_filter_kotlin_resolves_same_name_imported_superclass(self):
        kt_code = """
        package com.test
        import androidx.lifecycle.ViewModel

        class ViewModel : ViewModel() {
        }
        """
        output = filter_kotlin(kt_code, "ViewModel.kt")
        self.assertIn("public class ViewModel extends androidx.lifecycle.ViewModel", output)

    def test_filter_kotlin_secondary_constructor(self):
        kt_code = """
        class Person(val name: String) {
            constructor(name: String, age: Int) : this(name) {
                // constructor body
            }
        }
        """
        output = filter_kotlin(kt_code, "Person.kt")
        self.assertIn("public Person(String name, int age)", output)

    def test_filter_kotlin_data_class(self):
        kt_code = """
        data class SimpleUser(val username: String)
        """
        output = filter_kotlin(kt_code, "SimpleUser.kt")
        self.assertIn("public class SimpleUser", output)
        self.assertIn("public final String username;", output)

    def test_filter_kotlin_functional_interface(self):
        kt_code = """
        fun interface MyRunnable {
            fun run()
        }
        """
        output = filter_kotlin(kt_code, "MyRunnable.kt")
        self.assertIn("public interface MyRunnable", output)

    def test_filter_kotlin_delegated_property(self):
        kt_code = """
        class Item {
            val lazyName: String by lazy { "lazy_name" }
        }
        """
        output = filter_kotlin(kt_code, "Item.kt")
        self.assertIn("public final String lazyName;", output)

    def test_filter_kotlin_extension_property(self):
        kt_code = """
        val String.firstChar: Char get() = this[0]
        """
        output = filter_kotlin(kt_code, "StringExt.kt")
        self.assertIn("public static final char firstChar;", output)

    def test_filter_kotlin_prepends_file_directive(self):
        kt_code = "package com.example"
        output = filter_kotlin(kt_code, "Greeter.kt")
        self.assertTrue(output.startswith("/** @file */"))

    def test_cli_version(self):
        with patch('sys.argv', ['kotlin-doxygen', '--version']):
            stdout = io.StringIO()
            with patch('sys.stdout', stdout):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 0)
                self.assertIn("kotlin-doxygen version", stdout.getvalue())

    def test_cli_help(self):
        with patch('sys.argv', ['kotlin-doxygen', '--help']):
            stderr = io.StringIO()
            with patch('sys.stderr', stderr):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 0)
                self.assertIn("Kotlin Doxygen Filter/Generator", stderr.getvalue())

if __name__ == "__main__":
    unittest.main()
