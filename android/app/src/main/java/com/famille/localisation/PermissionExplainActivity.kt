package com.famille.localisation

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Écran INCITATIF (pas coercitif) : explique pourquoi « Toujours autoriser » aide, et ouvre
 * les réglages système de l'app. Si l'enfant refuse, on respecte — pas de relance en boucle.
 */
class PermissionExplainActivity : AppCompatActivity() {
    companion object {
        fun show(ctx: Context) = ctx.startActivity(
            Intent(ctx, PermissionExplainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(48, 96, 48, 48) }
        root.addView(TextView(this).apply {
            text = "Partage de position"; textSize = 22f
        })
        root.addView(TextView(this).apply {
            text = "Pour que ta famille voie ta position même quand l'app est fermée, choisis " +
                "« Toujours autoriser » dans les réglages. Tu peux mettre le partage en pause à tout moment."
            textSize = 15f; setPadding(0, 24, 0, 32)
        })
        root.addView(Button(this).apply {
            text = "Ouvrir les réglages"
            setOnClickListener {
                startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                    Uri.fromParts("package", packageName, null)))
            }
        })
        root.addView(Button(this).apply {
            text = "Plus tard"; setOnClickListener { finish() }   // refus respecté
        })
        setContentView(root)
    }
}
