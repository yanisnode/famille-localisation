import Foundation

/// Client HTTP minimal vers le backend famille.
enum Api {
    static let base = "https://famille.wifimobiletv.com/api/family"

    private static func post(_ path: String, _ body: [String: Any],
                             _ done: @escaping (Int, [String: Any]) -> Void) {
        var req = URLRequest(url: URL(string: base + path)!)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        req.timeoutInterval = 15
        URLSession.shared.dataTask(with: req) { data, resp, _ in
            let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
            let json = (data.flatMap { try? JSONSerialization.jsonObject(with: $0) }) as? [String: Any] ?? [:]
            done(code, json)
        }.resume()
    }

    /// Échange le token d'invitation (Universal Link) contre un device_token durable.
    static func enroll(inviteToken: String, done: @escaping (String?) -> Void) {
        post("/enroll/", ["invite_token": inviteToken, "platform": "ios"]) { code, json in
            done(code == 201 ? json["device_token"] as? String : nil)
        }
    }

    /// Remontée position + batterie. `done(false)` si le serveur refuse (partage coupé).
    static func ping(deviceToken: String, lat: Double, lon: Double, battery: Int,
                     done: @escaping (Bool) -> Void) {
        post("/ping/", ["device_token": deviceToken, "lat": lat, "lon": lon, "battery": battery]) { code, _ in
            done(code == 200)
        }
    }

    static func setSharing(deviceToken: String, on: Bool) {
        post("/sharing/", ["device_token": deviceToken, "on": on]) { _, _ in }
    }
}
