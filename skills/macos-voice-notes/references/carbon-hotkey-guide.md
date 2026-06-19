# Carbon Hotkey на macOS (Swift)

RegisterEventHotKey — легаси Carbon API для глобальных хоткеев. Не требует Accessibility.

## Когда использовать

- Нужен глобальный хоткей для SwiftUI MenuBarExtra приложения
- Нужно избежать Accessibility permission (CGEventTap требует)
- Достаточно toggle режима (нет keyUp)

## Ключевые правила

### 1. setActivationPolicy(.accessory) вместо LSUIElement

Если в Info.plist стоит `LSUIElement = true` — Carbon `RegisterEventHotKey` **не работает** на macOS 14+.

```swift
@main
struct MyApp: App {
    init() {
        NSApplication.shared.setActivationPolicy(.accessory)
    }
    // ...
}
```

Info.plist НЕ должен содержать `LSUIElement` ключ.

### 2. Только keyDown, нет keyUp

Carbon генерирует `kEventHotKeyPressed` (keyDown) и `kEventHotKeyReleased` (keyUp), но `kEventHotKeyReleased` **не работает** в современных macOS через InstallEventHandler. Только toggle.

### 3. Регистрация

```swift
import Carbon

private var hotKeyRef: EventHotKeyRef?

func setupHotkey() {
    let id = EventHotKeyID(signature: 0x564E, id: 1)
    let status = RegisterEventHotKey(
        UInt32(kVK_F5),       // keyCode: kVK_F5=96, kVK_Space=49
        UInt32(optionKey),    // modifiers: 0, optionKey, cmdKey, shiftKey, controlKey
        id,
        GetApplicationEventTarget(),
        0,
        &hotKeyRef
    )
    guard status == noErr else { return }

    var eventType = EventTypeSpec(
        eventClass: OSType(kEventClassKeyboard),
        eventKind: UInt32(kEventHotKeyPressed)
    )

    let selfPtr = Unmanaged.passUnretained(self).toOpaque()
    InstallEventHandler(
        GetApplicationEventTarget(),
        { _, _, refcon in
            let service = Unmanaged<MyClass>.fromOpaque(refcon!).takeUnretainedValue()
            DispatchQueue.main.async { service.action() }
            return noErr
        },
        1, &eventType, selfPtr, nil
    )
}
```

### 4. Push-to-talk (зажал/отпустил)

Carbon не подходит. Использовать CGEventTap + Accessibility:

```swift
let eventMask = (1 << CGEventType.keyDown.rawValue) | (1 << CGEventType.keyUp.rawValue)
let tap = CGEvent.tapCreate(
    tap: .cgSessionEventTap, place: .headInsertEventTap,
    options: .defaultTap,
    eventsOfInterest: CGEventMask(eventMask),
    callback: { proxy, type, event, refcon in
        if type == .keyDown { start() }
        else if type == .keyUp { stop() }
        return nil
    },
    userInfo: ptr
)
```

Требует: System Settings → Privacy → Accessibility.
