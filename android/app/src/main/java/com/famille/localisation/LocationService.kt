package com.famille.localisation

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleService

/**
 * Service premier plan avec NOTIFICATION PERMANENTE : l'enfant voit en continu que la position
 * est partagée, et un appui dessus ouvre l'écran pour mettre en pause. La position fine est
 * lue par WorkManager (LocationWorker) ; ce service garantit la visibilité + la vie en fond.
 */
class LocationService : LifecycleService() {
    companion object {
        private const val CHANNEL = "partage_position"
        private const val NOTIF_ID = 1001
    }

    override fun onBind(intent: Intent) = super.onBind(intent).let { null as IBinder? }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)
        startForeground(NOTIF_ID, buildNotification())
        LocationWorker.kickNow(applicationContext)     // 1er envoi tout de suite
        LocationWorker.schedule(applicationContext)    // puis remontées périodiques (15 min)
        return START_STICKY
    }

    private fun buildNotification(): Notification {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val ch = NotificationChannel(CHANNEL, "Partage de position", NotificationManager.IMPORTANCE_LOW)
            getSystemService(NotificationManager::class.java).createNotificationChannel(ch)
        }
        val open = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE)
        return NotificationCompat.Builder(this, CHANNEL)
            .setContentTitle("Position partagée avec la famille")
            .setContentText("Appuie pour mettre en pause")
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setOngoing(true).setContentIntent(open).build()
    }
}
