plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "com.famille.localisation"
    compileSdk = 34
    defaultConfig {
        applicationId = "com.famille.localisation"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }
    buildTypes { release { isMinifyEnabled = false } }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.security:security-crypto:1.1.0-alpha06")  // EncryptedSharedPreferences
    implementation("androidx.work:work-runtime-ktx:2.9.1")             // WorkManager
    implementation("androidx.lifecycle:lifecycle-process:2.8.4")       // ProcessLifecycleOwner
    implementation("androidx.lifecycle:lifecycle-service:2.8.4")
    implementation("com.google.android.gms:play-services-location:21.3.0")
}
