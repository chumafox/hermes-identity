import Foundation
import CoreAudio

func getDefaultInput() -> AudioDeviceID {
    var id = AudioDeviceID(0)
    var size = UInt32(MemoryLayout<AudioDeviceID>.size)
    var addr = AudioObjectPropertyAddress(
        mSelector: kAudioHardwarePropertyDefaultInputDevice,
        mScope: kAudioObjectPropertyScopeGlobal,
        mElement: kAudioObjectPropertyElementMain
    )
    AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size, &id)
    return id
}

func setDefaultInput(_ id: AudioDeviceID) {
    var dev = id
    var addr = AudioObjectPropertyAddress(
        mSelector: kAudioHardwarePropertyDefaultInputDevice,
        mScope: kAudioObjectPropertyScopeGlobal,
        mElement: kAudioObjectPropertyElementMain
    )
    AudioObjectSetPropertyData(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, UInt32(MemoryLayout<AudioDeviceID>.size), &dev)
}

func listDevices() -> [(AudioDeviceID, String, Bool)] {
    var size = UInt32(0)
    var addr = AudioObjectPropertyAddress(
        mSelector: kAudioHardwarePropertyDevices,
        mScope: kAudioObjectPropertyScopeGlobal,
        mElement: kAudioObjectPropertyElementMain
    )
    AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size)
    let count = Int(size) / MemoryLayout<AudioDeviceID>.size
    var ids = [AudioDeviceID](repeating: 0, count: count)
    AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size, &ids)
    
    let current = getDefaultInput()
    var result: [(AudioDeviceID, String, Bool)] = []
    
    for devId in ids {
        var nameSize = UInt32(MemoryLayout<CFString?>.size)
        var nameAddr = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyDeviceNameCFString,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain
        )
        var name: CFString? = nil
        AudioObjectGetPropertyData(devId, &nameAddr, 0, nil, &nameSize, &name)
        let devName = (name as String?) ?? "Unknown"
        
        // Check if it has input channels
        var chSize = UInt32(0)
        var chAddr = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyStreamConfiguration,
            mScope: kAudioObjectPropertyScopeInput,
            mElement: kAudioObjectPropertyElementMain
        )
        AudioObjectGetPropertyDataSize(devId, &chAddr, 0, nil, &chSize)
        if chSize > 0 {
            let isCurrent = devId == current
            result.append((devId, devName, isCurrent))
        }
    }
    return result
}

func findDevice(nameLike filter: String) -> AudioDeviceID? {
    for (id, name, _) in listDevices() {
        if name.lowercased().contains(filter.lowercased()) {
            return id
        }
    }
    return nil
}

let args = CommandLine.arguments

if args.contains("--list") {
    for (id, name, isCurrent) in listDevices() {
        print("\(isCurrent ? "▶" : " ") \(name) (id:\(id))")
    }
} else if let idx = args.firstIndex(of: "--set") {
    let nameFilter = args[idx + 1]
    if let devId = findDevice(nameLike: nameFilter) {
        setDefaultInput(devId)
        print("✓ Set default input to device matching '\(nameFilter)'")
    } else {
        print("✗ No input device matching '\(nameFilter)'")
        exit(1)
    }
} else if args.contains("--toggle") || args.contains("-t") {
    let current = getDefaultInput()
    let devices = listDevices()
    
    let curName = devices.first(where: { $0.0 == current })?.1 ?? ""
    if curName.lowercased().contains("blackhole") {
        if let micId = findDevice(nameLike: "microphone") {
            setDefaultInput(micId)
            print("✓ → Microphone")
        } else { print("✗ No mic found") }
    } else {
        if let bhId = findDevice(nameLike: "blackhole") {
            setDefaultInput(bhId)
            print("✓ → BlackHole 2ch")
        } else { print("✗ BlackHole not found") }
    }
} else {
    print("Usage: audiodev --list | --set <name> | --toggle")
}
