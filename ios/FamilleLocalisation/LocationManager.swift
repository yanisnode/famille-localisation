import CoreLocation
import UIKit

/// Localisation iOS : demande « Toujours », remonte via significant-change (économe en batterie),
/// et respecte un refus (écran explicatif qui PROPOSE d'ouvrir les réglages, sans forcer).
final class LocationManager: NSObject, CLLocationManagerDelegate {
    static let shared = LocationManager()
    private let manager = CLLocationManager()

    override init() {
        super.init()
        manager.delegate = self
        manager.allowsBackgroundLocationUpdates = true
        manager.pausesLocationUpdatesAutomatically = true
    }

    func start() {
        guard SecureStore.isEnrolled else { return }
        manager.requestAlwaysAuthorization()
        manager.startMonitoringSignificantLocationChanges()
    }

    /// Vérif douce au premier plan : si pas « Toujours », propose les réglages sans insister.
    func checkPermissionSoftly() {
        switch manager.authorizationStatus {
        case .authorizedAlways: start()
        case .notDetermined: manager.requestAlwaysAuthorization()
        default: offerSettings()
        }
    }

    private func offerSettings() {
        guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
        let alert = UIAlertController(
            title: "Partage de position",
            message: "Choisis « Toujours » pour partager ta position avec ta famille même app fermée. "
                   + "Tu peux mettre en pause quand tu veux.",
            preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Ouvrir les réglages", style: .default) { _ in
            UIApplication.shared.open(url)
        })
        alert.addAction(UIAlertAction(title: "Plus tard", style: .cancel))   // refus respecté
        UIApplication.shared.connectedScenes
            .compactMap { ($0 as? UIWindowScene)?.keyWindow?.rootViewController }
            .first?.present(alert, animated: true)
    }

    func locationManager(_ m: CLLocationManager, didUpdateLocations locs: [CLLocation]) {
        guard let token = SecureStore.deviceToken(), let loc = locs.last else { return }
        UIDevice.current.isBatteryMonitoringEnabled = true
        let battery = Int(max(0, UIDevice.current.batteryLevel) * 100)
        Api.ping(deviceToken: token, lat: loc.coordinate.latitude,
                 lon: loc.coordinate.longitude, battery: battery) { _ in }
    }
}
