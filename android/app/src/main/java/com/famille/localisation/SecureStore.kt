package com.famille.localisation

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Stockage CHIFFRÉ (EncryptedSharedPreferences, clé Keystore) : device_token + nom de l'enfant
 * + drapeau « partage activé ». Survit au redémarrage. Rien de caché : l'app affiche l'état.
 */
object SecureStore {
    private const val FILE = "famille_secure"
    private const val KEY_TOKEN = "device_token"
    private const val KEY_LABEL = "label"
    private const val KEY_SHARING = "sharing_on"

    private fun prefs(ctx: Context) =
        MasterKey.Builder(ctx).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build().let { key ->
            EncryptedSharedPreferences.create(
                ctx, FILE, key,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
            )
        }

    fun saveDevice(ctx: Context, token: String, label: String) =
        prefs(ctx).edit().putString(KEY_TOKEN, token).putString(KEY_LABEL, label)
            .putBoolean(KEY_SHARING, true).apply()

    fun deviceToken(ctx: Context): String? = prefs(ctx).getString(KEY_TOKEN, null)
    fun label(ctx: Context): String = prefs(ctx).getString(KEY_LABEL, "") ?: ""
    fun isEnrolled(ctx: Context): Boolean = !deviceToken(ctx).isNullOrBlank()

    fun sharingOn(ctx: Context): Boolean = prefs(ctx).getBoolean(KEY_SHARING, true)
    fun setSharing(ctx: Context, on: Boolean) = prefs(ctx).edit().putBoolean(KEY_SHARING, on).apply()

    fun clear(ctx: Context) = prefs(ctx).edit().clear().apply()
}
