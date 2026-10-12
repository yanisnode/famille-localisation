import BackgroundTasks
import CoreLocation

/// Tâche de fond périodique (BGAppRefreshTask) : complément au significant-change,
/// cadencée par iOS selon la batterie et les habitudes d'usage.
enum BackgroundRefresh {
    static let taskId = "com.famille.localisation.refresh"

    static func register() {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: taskId, using: nil) { task in
            handle(task as! BGAppRefreshTask)
        }
    }

    static func schedule() {
        let req = BGAppRefreshTaskRequest(identifier: taskId)
        req.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60)
        try? BGTaskScheduler.shared.submit(req)
    }

    private static func handle(_ task: BGAppRefreshTask) {
        schedule()                               // replanifie la prochaine
        LocationManager.shared.start()
        task.setTaskCompleted(success: true)
    }
}
