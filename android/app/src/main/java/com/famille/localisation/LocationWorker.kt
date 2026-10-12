package com.famille.localisation

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.BatteryManager
import androidx.core.content.ContextCompat
import androidx.work.*
import com.google.android.gms.location.LocationServices
import com.google.android.gms.tasks.Tasks
import java.util.concurrent.TimeUnit

/**
 * Remontée périodique (WorkManager, min OS 15 min) : position (Fused, précise) + batterie + apps.
 * Si l'enfant a mis en pause (drapeau local) OU si le serveur refuse → on n'insiste pas.
 */
class LocationWorker(ctx: Context, params: WorkerParameters) : Worker(ctx, params) {

    override fun doWork(): Result {
        val ctx = applicationContext
        val token = SecureStore.deviceToken(ctx) ?: return Result.success()
        if (!SecureStore.sharingOn(ctx)) return Result.success()      // en pause : rien
        val loc = lastLocation() ?: return Result.retry()
        val battery = (ctx.getSystemService(Context.BATTERY_SERVICE) as BatteryManager)
            .getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        Api.ping(token, loc.first, loc.second, battery, installedApps())
        return Result.success()
    }

    private fun lastLocation(): Pair<Double, Double>? {
        if (ContextCompat.checkSelfPermission(applicationContext,
                Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) return null
        return try {
            val client = LocationServices.getFusedLocationProviderClient(applicationContext)
            val l = Tasks.await(client.lastLocation) ?: return null
            l.latitude to l.longitude
        } catch (e: Exception) { null }
    }

    /** Liste des apps installées — au su de l'enfant (affichée dans l'app et côté parent). */
    private fun installedApps(): List<Pair<String, String>> {
        val pm = applicationContext.packageManager
        return pm.getInstalledApplications(0).map { it.packageName to pm.getApplicationLabel(it).toString() }
    }

    companion object {
        private const val WORK = "famille_ping"
        fun schedule(ctx: Context) {
            val req = PeriodicWorkRequestBuilder<LocationWorker>(15, TimeUnit.MINUTES)
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .build()
            WorkManager.getInstance(ctx).enqueueUniquePeriodicWork(WORK, ExistingPeriodicWorkPolicy.KEEP, req)
        }
    }
}
