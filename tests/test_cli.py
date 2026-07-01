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

    def test_split_params(self):
        self.assertEqual(split_params("a: Int, b: String"), ["a: Int", "b: String"])
        self.assertEqual(split_params("map: Map<String, Int>, name: String"), ["map: Map<String, Int>", "name: String"])
        self.assertEqual(split_params("x: Int = 0, y: Int = 1"), ["x: Int = 0", "y: Int = 1"])

    def test_translate_param_list(self):
        self.assertEqual(translate_param_list("a: Int, b: String?"), "int a, String b")
        self.assertEqual(translate_param_list("val accp: Long, virtualAor: String? = null"), "long accp, String virtualAor")
        self.assertEqual(translate_param_list("map: Map<String, Int>"), "Map<String, Int> map")

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
