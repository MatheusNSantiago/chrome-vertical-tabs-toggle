import AppKit
import ApplicationServices
import Foundation

enum HostError: Error, LocalizedError {
    case invalidMessage
    case unsupportedCommand
    case unsupportedLabels
    case accessibilityPermissionMissing
    case chromeNotFound
    case sidebarToggleNotFound
    case pressFailed
    case stateChangeTimedOut

    var errorDescription: String? {
        switch self {
        case .invalidMessage:
            return "invalid Native Messaging request"
        case .unsupportedCommand:
            return "unsupported command"
        case .unsupportedLabels:
            return "unsupported sidebar labels"
        case .accessibilityPermissionMissing:
            return "grant Accessibility access to Chrome Vertical Tabs Toggle in System Settings"
        case .chromeNotFound:
            return "active Chrome or Chromium window was not found"
        case .sidebarToggleNotFound:
            return "Chrome vertical tab toggle was not found"
        case .pressFailed:
            return "Chrome rejected the sidebar action"
        case .stateChangeTimedOut:
            return "Chrome did not change the vertical tab sidebar state"
        }
    }
}

struct Labels: Decodable {
    let schemaVersion: Int
    let collapse: [String]
    let expand: [String]

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case collapse
        case expand
    }
}

struct Request: Decodable {
    let command: String
}

func readExactly(_ length: Int, from input: FileHandle) throws -> Data {
    var data = Data()
    while data.count < length {
        let chunk = input.readData(ofLength: length - data.count)
        guard !chunk.isEmpty else { throw HostError.invalidMessage }
        data.append(chunk)
    }
    return data
}

func readRequest() throws -> Request {
    let input = FileHandle.standardInput
    let header = try readExactly(4, from: input)
    let bytes = [UInt8](header)
    let size = UInt32(bytes[0])
        | UInt32(bytes[1]) << 8
        | UInt32(bytes[2]) << 16
        | UInt32(bytes[3]) << 24
    let payload = try readExactly(Int(size), from: input)
    return try JSONDecoder().decode(Request.self, from: payload)
}

func writeResponse(_ response: [String: String]) {
    let payload = try! JSONSerialization.data(withJSONObject: response)
    var size = UInt32(payload.count).littleEndian
    let output = FileHandle.standardOutput
    withUnsafeBytes(of: &size) { output.write(Data($0)) }
    output.write(payload)
}

func readLabels() throws -> Labels {
    let labelsURL = Bundle.main.url(forResource: "sidebar-labels", withExtension: "json")!
    let labels = try JSONDecoder().decode(
        Labels.self,
        from: Data(contentsOf: labelsURL)
    )
    guard labels.schemaVersion == 1 else { throw HostError.unsupportedLabels }
    return labels
}

func attribute<T>(_ element: AXUIElement, _ name: CFString) -> T? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(element, name, &value) == .success else { return nil }
    return value as? T
}

let chromeBundleIdentifiers = Set([
    "com.google.Chrome",
    "com.google.Chrome.beta",
    "com.google.Chrome.dev",
    "com.google.Chrome.canary",
    "com.google.chrome.for.testing",
    "org.chromium.Chromium",
])

func runningBrowsers() -> [NSRunningApplication] {
    return NSWorkspace.shared.runningApplications.filter {
        chromeBundleIdentifiers.contains($0.bundleIdentifier ?? "")
    }
}

func activeChromeWindow() throws -> AXUIElement {
    guard let chrome = runningBrowsers().first(where: \.isActive) else {
        throw HostError.chromeNotFound
    }

    let application = AXUIElementCreateApplication(chrome.processIdentifier)
    if let focused: AXUIElement = attribute(application, kAXFocusedWindowAttribute as CFString) {
        return focused
    }
    if let windows: [AXUIElement] = attribute(
        application,
        kAXWindowsAttribute as CFString
    ), let window = windows.first {
        return window
    }
    throw HostError.chromeNotFound
}

func chromeWindows() -> [AXUIElement] {
    return runningBrowsers().flatMap { browser in
        let application = AXUIElementCreateApplication(browser.processIdentifier)
        let windows: [AXUIElement]? = attribute(
            application,
            kAXWindowsAttribute as CFString
        )
        return windows ?? []
    }
}

func sidebarButton(in root: AXUIElement, labels: Labels) -> (AXUIElement, String)? {
    let knownLabels = Set(labels.collapse).union(labels.expand)
    var pending = [root]

    while let element = pending.popLast() {
        let role: String? = attribute(element, kAXRoleAttribute as CFString)
        if role == kAXWebAreaRole as String {
            continue
        }
        let children: [AXUIElement]? = attribute(
            element,
            kAXChildrenAttribute as CFString
        )
        pending.append(contentsOf: children ?? [])
        guard role == kAXButtonRole as String else { continue }

        let title: String? = attribute(element, kAXTitleAttribute as CFString)
        let description: String? = attribute(
            element,
            kAXDescriptionAttribute as CFString
        )
        let label = [title, description]
            .compactMap { $0 }
            .first(where: knownLabels.contains)
        if let label = label {
            return (element, label)
        }
    }
    return nil
}

func currentState(for label: String, labels: Labels) -> String {
    return Set(labels.expand).contains(label) ? "collapsed" : "expanded"
}

func waitForState(
    in window: AXUIElement,
    expectedState: String,
    labels: Labels
) throws -> String {
    let deadline = Date().addingTimeInterval(1.5)
    while Date() < deadline {
        if let (_, label) = sidebarButton(in: window, labels: labels),
           currentState(for: label, labels: labels) == expectedState {
            return expectedState
        }
        Thread.sleep(forTimeInterval: 0.05)
    }
    throw HostError.stateChangeTimedOut
}

func toggleActiveSidebar(labels: Labels) throws -> String {
    let window = try activeChromeWindow()
    guard let (button, label) = sidebarButton(in: window, labels: labels) else {
        throw HostError.sidebarToggleNotFound
    }
    let expectedState = currentState(for: label, labels: labels) == "expanded"
        ? "collapsed"
        : "expanded"
    guard AXUIElementPerformAction(button, kAXPressAction as CFString) == .success else {
        throw HostError.pressFailed
    }
    return try waitForState(in: window, expectedState: expectedState, labels: labels)
}

func collapseSidebars(labels: Labels) throws -> String {
    let windowsWithButtons = chromeWindows().compactMap { window in
        sidebarButton(in: window, labels: labels).map { (window, $0.0, $0.1) }
    }
    guard !windowsWithButtons.isEmpty else {
        throw HostError.sidebarToggleNotFound
    }

    for (window, button, label) in windowsWithButtons {
        if currentState(for: label, labels: labels) == "collapsed" {
            continue
        }
        guard AXUIElementPerformAction(button, kAXPressAction as CFString) == .success else {
            throw HostError.pressFailed
        }
        _ = try waitForState(in: window, expectedState: "collapsed", labels: labels)
    }
    return "collapsed"
}

func controlSidebar(command: String) throws -> String {
    let commandIsSupported = command == "toggle" || command == "collapse"
    guard commandIsSupported else { throw HostError.unsupportedCommand }

    let promptKey = kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String
    guard AXIsProcessTrustedWithOptions([promptKey: true] as CFDictionary) else {
        throw HostError.accessibilityPermissionMissing
    }

    let labels = try readLabels()
    if command == "toggle" {
        return try toggleActiveSidebar(labels: labels)
    }
    return try collapseSidebars(labels: labels)
}

do {
    let request = try readRequest()
    writeResponse(["state": try controlSidebar(command: request.command)])
} catch {
    writeResponse(["error": error.localizedDescription])
}
