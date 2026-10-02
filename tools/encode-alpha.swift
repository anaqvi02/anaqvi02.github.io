// macOS HEVC-alpha encoder with a bounded base-layer bitrate.
// swift tools/encode-alpha.swift input-prores.mov output.mov 768 1800000
import Foundation
import AVFoundation
import VideoToolbox

let args = CommandLine.arguments
guard args.count == 5, let size = Int(args[3]), let bitrate = Int(args[4]) else {
    fatalError("Usage: encode-alpha.swift source.mov output.mov size bitrate")
}
let asset = AVURLAsset(url: URL(fileURLWithPath: args[1]))
let track = asset.tracks(withMediaType: .video).first!
let reader = try AVAssetReader(asset: asset)
let output = AVAssetReaderTrackOutput(track: track, outputSettings: [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA
])
output.alwaysCopiesSampleData = false
reader.add(output)
let destination = URL(fileURLWithPath: args[2])
if FileManager.default.fileExists(atPath: destination.path) {
    try FileManager.default.removeItem(at: destination)
}
let writer = try AVAssetWriter(outputURL: destination, fileType: .mov)
writer.shouldOptimizeForNetworkUse = true
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.hevcWithAlpha,
    AVVideoWidthKey: size,
    AVVideoHeightKey: size,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: bitrate,
        AVVideoMaxKeyFrameIntervalKey: max(1, Int(track.nominalFrameRate * 4)),
        AVVideoExpectedSourceFrameRateKey: track.nominalFrameRate,
        kVTCompressionPropertyKey_TargetQualityForAlpha as String: 0.75
    ]
])
input.expectsMediaDataInRealTime = false
guard writer.canAdd(input) else {
    throw NSError(domain: "hero-alpha", code: 2, userInfo: [NSLocalizedDescriptionKey: "HEVC alpha is unavailable in this container"])
}
writer.add(input)
guard writer.startWriting() else { throw writer.error! }
writer.startSession(atSourceTime: .zero)
guard reader.startReading() else { throw reader.error! }
let complete = DispatchSemaphore(value: 0)
let queue = DispatchQueue(label: "hero-alpha-encode")
input.requestMediaDataWhenReady(on: queue) {
    while input.isReadyForMoreMediaData {
        if let sample = output.copyNextSampleBuffer() {
            if !input.append(sample) {
                reader.cancelReading()
                input.markAsFinished()
                complete.signal()
                return
            }
        } else {
            input.markAsFinished()
            writer.finishWriting { complete.signal() }
            return
        }
    }
}
complete.wait()
guard writer.status == .completed else {
    throw writer.error ?? NSError(domain: "hero-alpha",code: 1)
}
if reader.status == .failed { throw reader.error! }
print("Encoded HEVC alpha", size, bitrate, destination.lastPathComponent)
