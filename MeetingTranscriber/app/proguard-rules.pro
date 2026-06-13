# kotlinx.serialization keeps generated serializers
-keepclassmembers,allowshrinking,allowobfuscation class **$$serializer { *; }
-keepclassmembers class * { @kotlinx.serialization.Serializable <fields>; }
