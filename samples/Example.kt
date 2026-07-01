package com.example.kotlin

/**
 * این یک کلاس نمونه برای تست مبدل داکسیژن است.
 * This is a sample class for testing Doxygen conversion.
 */
@Deprecated("Use new API")
class Example(val primaryVal: String, var primaryVar: Int?) {

    /**
     * یک متغیر همراه با توضیحات یونیکد.
     * A variable with Unicode comment.
     */
    var name: String = "Default"
        get() = field
        set(value) { field = value }

    /**
     * ثابتی در کلاس.
     */
    val constantValue: Double = 3.14

    /**
     * سازنده ثانویه کلاس.
     * Secondary constructor.
     */
    constructor(primaryVal: String) : this(primaryVal, null) {
        println("Secondary constructor called")
    }

    /**
     * یک تابع نمونه.
     * A sample function with arguments.
     * @param input ورودی تست.
     * @return مقدار خروجی.
     */
    fun processData(input: List<String>): Map<String, Int> {
        return mapOf()
    }

    /**
     * یک تابع تعلیقی نمونه.
     * A sample suspend function.
     */
    suspend fun fetchAsync(): Boolean {
        return true
    }

    /**
     * شیء همراه با متدهای استاتیک.
     * Companion object with static methods.
     */
    companion object Factory {
        /**
         * ایجاد یک نمونه جدید.
         */
        fun create(): Example = Example("Factory", 10)
    }
}

/**
 * یک کلاس داده برای ذخیره اطلاعات.
 * A data class to store info.
 */
data class User(val id: Long, val email: String)

/**
 * یک اینترفیس نمونه.
 * A sample interface.
 */
interface Service {
    fun execute()
}

/**
 * یک انوم نمونه.
 * A sample enum.
 */
enum class Direction {
    NORTH, SOUTH, EAST, WEST
}

/**
 * یک تابع الحاقی برای کلاس String.
 * An extension function for the String class.
 */
fun String.shout(): String {
    return this.uppercase() + "!"
}

/**
 * یک اینترفیس کاربردی (SAM).
 * A functional interface.
 */
fun interface MyRunnable {
    fun run()
}

/**
 * ویژگی‌های الحاقی و ویژگی‌های وکالتی.
 */
val lazyProperty: String by lazy { "Lazy Hello" }

val String.firstChar: Char
    get() = this[0]

val <T> List<T>.lastIndex: Int
    get() = size - 1
