package com.famille.localisation

import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Client HTTP minimal (sans lib externe) vers le backend famille. */
object Api {
    const val BASE = "https://famille.wifimobiletv.com/api/family"

    private fun post(path: String, body: JSONObject): JSONObject {
        val c = (URL("$BASE$path").openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"; doOutput = true
            setRequestProperty("Content-Type", "application/json")
            connectTimeout = 15000; readTimeout = 15000
        }
        c.outputStream.use { it.write(body.toString().toByteArray()) }
        val code = c.responseCode
        val text = (if (code in 200..299) c.inputStream else c.errorStream)
            .bufferedReader().use { it.readText() }
        return JSONObject(text.ifBlank { "{}" }).put("_status", code)
    }

    /** Échange le token d'invitation (lien) contre un device_token durable. Renvoie (token, nom) ou null. */
    fun enroll(inviteToken: String): Pair<String, String>? {
        val r = post("/enroll/", JSONObject().put("invite_token", inviteToken).put("platform", "android"))
        if (r.optInt("_status") != 201) return null
        return r.optString("device_token") to r.optString("label", "")
    }

    /** Remontée position + batterie + apps. false si le serveur refuse (partage coupé). */
    fun ping(deviceToken: String, lat: Double, lon: Double, battery: Int, apps: List<Pair<String, String>>): Boolean {
        val arr = JSONArray()
        apps.forEach { arr.put(JSONObject().put("package", it.first).put("name", it.second)) }
        val r = post("/ping/", JSONObject()
            .put("device_token", deviceToken).put("lat", lat).put("lon", lon)
            .put("battery", battery).put("apps", arr))
        return r.optInt("_status") == 200
    }

    fun setSharing(deviceToken: String, on: Boolean) =
        post("/sharing/", JSONObject().put("device_token", deviceToken).put("on", on))
}
