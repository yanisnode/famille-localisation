import UIKit

/// Capte le token d'invitation reçu par Universal Link (NSUserActivity), au lancement
/// et à chaud. À chaque retour au premier plan, vérifie la permission de localisation.
class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession,
               options connectionOptions: UIScene.ConnectionOptions) {
        for activity in connectionOptions.userActivities { handle(activity) }
    }

    func scene(_ scene: UIScene, continue userActivity: NSUserActivity) { handle(userActivity) }

    func sceneWillEnterForeground(_ scene: UIScene) {
        LocationManager.shared.checkPermissionSoftly()
    }

    /// Universal Link : https://famille.wifimobiletv.com/enroll?token=XXX → enrôlement.
    private func handle(_ activity: NSUserActivity) {
        guard activity.activityType == NSUserActivityTypeBrowsingWeb,
              let url = activity.webpageURL,
              let token = URLComponents(url: url, resolvingAgainstBaseURL: false)?
                  .queryItems?.first(where: { $0.name == "token" })?.value,
              !SecureStore.isEnrolled else { return }
        Api.enroll(inviteToken: token) { deviceToken in
            guard let deviceToken else { return }
            SecureStore.saveDeviceToken(deviceToken)
            LocationManager.shared.start()
        }
    }
}
