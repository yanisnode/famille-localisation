package com.famille.localisation

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.ProcessLifecycleOwner

/**
 * App enfant — parcours transparent et consenti :
 *   1) Ouverture du lien d'invitation (App Link) → écran d'accueil + CONSENTEMENT (ce qui est partagé).
 *   2) L'enfant accepte → enrôlement (device_token) → demande de permission de localisation.
 *   3) Écran de STATUT : « Actif » avec notification permanente, bouton PAUSE ; ou « En pause » avec REPRENDRE.
 * Un refus de permission est respecté (écran explicatif, pas de relance forcée).
 */
class MainActivity : AppCompatActivity() {

    private var inviteToken: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        inviteToken = intent?.data?.getQueryParameter("token")
        ProcessLifecycleOwner.get().lifecycle.addObserver(object : DefaultLifecycleObserver {
            override fun onStart(owner: LifecycleOwner) { if (SecureStore.isEnrolled(this@MainActivity)) ensurePermissionThenRun() }
        })
        render()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        inviteToken = intent.data?.getQueryParameter("token") ?: inviteToken
        render()
    }

    override fun onResume() { super.onResume(); render() }

    // ───────────────────────── Rendu selon l'état ─────────────────────────
    private fun render() {
        when {
            SecureStore.isEnrolled(this) -> statusScreen()
            inviteToken != null -> consentScreen(inviteToken!!)
            else -> infoScreen()
        }
    }

    private fun screen(): LinearLayout {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(56, 120, 56, 56)
            setBackgroundColor(Color.parseColor("#F8FAFC"))
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
        }
        setContentView(root)
        return root
    }

    private fun title(t: String) = TextView(this).apply { text = t; textSize = 23f; setTextColor(Color.parseColor("#0F172A")) }
    private fun body(t: String) = TextView(this).apply { text = t; textSize = 15f; setTextColor(Color.parseColor("#334155")); setPadding(0, 24, 0, 24) }
    private fun primary(t: String, onClick: () -> Unit) = Button(this).apply {
        text = t; setBackgroundColor(Color.parseColor("#185FA5")); setTextColor(Color.WHITE)
        setOnClickListener { onClick() }
    }
    private fun ghost(t: String, onClick: () -> Unit) = Button(this).apply {
        text = t; setBackgroundColor(Color.parseColor("#FFFFFF")); setTextColor(Color.parseColor("#334155"))
        setOnClickListener { onClick() }
    }

    // 1) Lien sans invitation ni enrôlement — saisie manuelle du lien/code
    private fun infoScreen() {
        val r = screen()
        r.addView(title("Localisation famille"))
        r.addView(body("Colle ci-dessous le lien d'invitation envoyé par ton parent, puis appuie sur « Rejoindre la famille »."))
        val input = EditText(this).apply {
            hint = "Colle le lien ou le code ici"
            setTextColor(Color.parseColor("#0F172A"))
            setHintTextColor(Color.parseColor("#94A3B8"))
            setSingleLine(false)
        }
        r.addView(input)
        r.addView(primary("Rejoindre la famille") {
            val token = extractToken(input.text?.toString().orEmpty().trim())
            if (token.isNullOrEmpty())
                Toast.makeText(this, "Lien ou code invalide. Recolle le lien complet.", Toast.LENGTH_LONG).show()
            else { inviteToken = token; render() }   // → écran de consentement
        })
    }

    /** Accepte un lien complet (…/enroll?token=XXX) OU un code brut collé seul. */
    private fun extractToken(raw: String): String? {
        if (raw.isEmpty()) return null
        return try {
            Uri.parse(raw).getQueryParameter("token")
                ?: if (!raw.contains("/") && !raw.contains("?")) raw else null
        } catch (e: Exception) {
            if (!raw.contains("/") && !raw.contains("?")) raw else null
        }
    }

    // 2) Accueil + consentement
    private fun consentScreen(token: String) {
        val r = screen()
        r.addView(title("Rejoindre la famille"))
        r.addView(body("Ton parent t'invite à partager ta position avec ta famille.\n\n" +
            "Ce qui sera partagé :\n" +
            "•  Ta position\n•  Les applications installées\n•  Ta batterie\n\n" +
            "Tu peux mettre le partage en pause quand tu veux."))
        r.addView(primary("J'accepte et je partage") {
            Thread {
                val res = Api.enroll(token)
                runOnUiThread {
                    if (res != null) {
                        SecureStore.saveDevice(this, res.first, res.second)
                        ensurePermissionThenRun(); render()
                    } else Toast.makeText(this, "Invitation invalide ou déjà utilisée.", Toast.LENGTH_LONG).show()
                }
            }.start()
        })
        r.addView(ghost("Non merci") { finish() })
    }

    // 3) Statut (actif / en pause)
    private fun statusScreen() {
        val r = screen()
        val on = SecureStore.sharingOn(this)
        r.addView(title(if (on) "Partage actif" else "Partage en pause"))
        r.addView(body(
            if (on) "Bonjour ${SecureStore.label(this)} 👋\n\nTa famille voit ta position. Une notification reste affichée tant que le partage est actif."
            else "Ta position n'est plus envoyée. Ta famille voit « en pause ». Tu peux reprendre quand tu veux."
        ))
        if (on) r.addView(ghost("⏸  Mettre en pause") { setSharing(false) })
        else r.addView(primary("▶  Reprendre le partage") { setSharing(true) })
    }

    private fun setSharing(on: Boolean) {
        SecureStore.setSharing(this, on)
        val token = SecureStore.deviceToken(this)
        if (token != null) Thread { Api.setSharing(token, on) }.start()
        if (on) ensurePermissionThenRun() else stopService(Intent(this, LocationService::class.java))
        render()
    }

    // ───────────────────────── Permission (douce) ─────────────────────────
    private fun hasFine() = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
    private fun hasBackground() = Build.VERSION.SDK_INT < Build.VERSION_CODES.Q ||
        ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_BACKGROUND_LOCATION) == PackageManager.PERMISSION_GRANTED

    private fun ensurePermissionThenRun() {
        if (!SecureStore.isEnrolled(this) || !SecureStore.sharingOn(this)) return
        if (hasFine() && hasBackground()) { startLocationService(); return }
        if (!hasFine()) {
            val perms = mutableListOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) perms.add(Manifest.permission.POST_NOTIFICATIONS)
            requestPermissions(perms.toTypedArray(), 1)
        } else {
            PermissionExplainActivity.show(this)  // demande « Toujours » via les réglages, sans forcer
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (hasFine()) { if (!hasBackground()) PermissionExplainActivity.show(this) else startLocationService() }
    }

    private fun startLocationService() {
        val i = Intent(this, LocationService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(i) else startService(i)
    }
}
